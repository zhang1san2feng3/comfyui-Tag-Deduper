import { app } from "../../../scripts/app.js";

app.registerExtension({
	name: "TagFilter.UI",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "TagFilterDeduper") {
			
			// 1. 拦截节点创建事件
			const onNodeCreated = nodeType.prototype.onNodeCreated;
			nodeType.prototype.onNodeCreated = function () {
				onNodeCreated?.apply(this, arguments);

				// 兜底保护：确保所有控件都有 options 对象
				if (this.widgets) {
					this.widgets.forEach(w => w.options = w.options || {});
				}
				
				// ★ 修复点 1：安全重写 onWidgetChanged，必须保留系统原有的回调，否则会破坏 V2 底层
				const origOnWidgetChanged = this.onWidgetChanged;
				this.onWidgetChanged = function (name, value, oldValue, widget) {
					// 先执行系统原生的 changed 逻辑
					if (origOnWidgetChanged) {
						origOnWidgetChanged.apply(this, arguments);
					}
					
					// 模块平行黑名单
					const groups = ["Character", "Style", "Outfit", "Custom"];
					for (const g of groups) {
						if (name === `enable_${g}`) {
							const widgets = this.widgets.filter(w => w.name === `partial_${g}` || w.name === `preset_${g}`);
							widgets.forEach(w => {
								w.options = w.options || {}; 
								w.disabled = !value;
							});
						}
					}

					// 智能层级提纯
					if (name === "purify_degrees") {
						const purifyWidgets = this.widgets.filter(w => w.name === "purify_keywords" || w.name === "size_modifiers_preset");
						purifyWidgets.forEach(w => {
							w.options = w.options || {}; 
							w.disabled = !value;
						});
					}
				};

				// 节点诞生时，强行把所有总开关设为 false (关闭)
				const groups = ["Character", "Style", "Outfit", "Custom"];
				groups.forEach(g => {
					const enableWidget = this.widgets.find(w => w.name === `enable_${g}`);
					if (enableWidget) {
						enableWidget.value = false; 
						const subWidgets = this.widgets.filter(w => w.name === `partial_${g}` || w.name === `preset_${g}`);
						subWidgets.forEach(w => w.disabled = true);
					}
				});

				// 强行关闭并锁死第 5 个提纯模块
				const purifyWidget = this.widgets.find(w => w.name === "purify_degrees");
				if (purifyWidget) {
					purifyWidget.value = false; 
					const purifySubWidgets = this.widgets.filter(w => w.name === "purify_keywords" || w.name === "size_modifiers_preset");
					purifySubWidgets.forEach(w => w.disabled = true);
				}
			};

			// 2. 拦截配置载入事件
			const onConfigure = nodeType.prototype.onConfigure;
			nodeType.prototype.onConfigure = function () {
				onConfigure?.apply(this, arguments);

				if (this.widgets) {
					this.widgets.forEach(w => w.options = w.options || {});
				}
				
				// 载入已有工作流数据后，根据恢复的开关状态再次校准锁定效果
				const groups = ["Character", "Style", "Outfit", "Custom"];
				groups.forEach(g => {
					const enableWidget = this.widgets.find(w => w.name === `enable_${g}`);
					if (enableWidget && this.onWidgetChanged) {
						// ★ 修复点 2（最致命的报错源）：必须完整传入 4 个参数 (name, value, oldValue, widget)
						this.onWidgetChanged(`enable_${g}`, enableWidget.value, enableWidget.value, enableWidget);
					}
				});

				const purifyWidget = this.widgets.find(w => w.name === "purify_degrees");
				if (purifyWidget && this.onWidgetChanged) {
					// ★ 修复点 3（最致命的报错源）：必须完整传入 4 个参数 (name, value, oldValue, widget)
					this.onWidgetChanged("purify_degrees", purifyWidget.value, purifyWidget.value, purifyWidget);
				}
			};

		}
	},
});