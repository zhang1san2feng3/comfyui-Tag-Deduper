import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

app.registerExtension({
    name: "ComfyUI.CustomTagging.PaginatedText",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "PaginatedTextViewer") {

            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                try {
                    const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                    
                    this.textsData = []; 
                    this.imagesData = []; 
                    this.size = [420, 200];

                    // 1. 显示开关
                    const showImgWidgetRes = ComfyWidgets["BOOLEAN"](this, "显示对应图片 (Show Image)", ["BOOLEAN", { default: false }], app);
                    const showImgWidget = showImgWidgetRes.widget;
                    showImgWidget.value = false;
                    
                    showImgWidget.callback = (v) => {
                        const isVisible = !!v;
                        if (this.imgElement) this.imgElement.style.display = isVisible ? "block" : "none";
                        if (this.imgWidget) this.imgWidget.computeSize = () => isVisible ? [this.size[0], 210] : [this.size[0], 0];
                        
                        if (isVisible) {
                            this.size[1] += 210;
                        } else {
                            this.size[1] = Math.max(this.size[1] - 210, 200); 
                        }

                        this.setSize(this.size); 
                        this.onResize(this.size);
                        if (app.graph) app.graph.setDirtyCanvas(true, true);
                    };

                    // 2. 页码器
                    const pageWidgetRes = ComfyWidgets["INT"](this, "跳转页码 (Page)", ["INT", { default: 1, min: 1, max: 1, step: 1 }], app);
                    const pageWidget = pageWidgetRes.widget;
                    pageWidget.callback = (v) => {
                        if (!this.textsData || this.textsData.length === 0) return;
                        let p = parseInt(v, 10);
                        if (isNaN(p)) p = 1;
                        p = Math.max(1, Math.min(p, this.textsData.length));
                        pageWidget.value = p;
                        this.updateDisplay(p - 1);
                    };

                    // 3. 图像容器
                    const imgDiv = document.createElement("div");
                    Object.assign(imgDiv.style, { width: "100%", height: "200px", display: "none", textAlign: "center", margin: "6px 0" });
                    const imgEl = document.createElement("img");
                    Object.assign(imgEl.style, { maxHeight: "100%", maxWidth: "100%", objectFit: "contain", borderRadius: "4px", border: "1px solid #353535" });
                    imgDiv.appendChild(imgEl);
                    this.imgElement = imgDiv;
                    
                    if (this.addDOMWidget) {
                        this.imgWidget = this.addDOMWidget("image_preview", "view", imgDiv);
                        this.imgWidget.computeSize = () => [this.size[0], 0];
                    }

                    // 4. 文本域
                    const textWidgetRes = ComfyWidgets["STRING"](this, "text_display", ["STRING", { multiline: true }], app);
                    const textWidget = textWidgetRes.widget;
                    this.textWidget = textWidget;
                    
                    requestAnimationFrame(() => {
                        if (textWidget.inputEl) {
                            textWidget.inputEl.readOnly = true;
                            Object.assign(textWidget.inputEl.style, { 
                                boxSizing: "border-box", 
                                backgroundColor: "var(--comfy-input-bg)", 
                                color: "var(--input-text)", 
                                fontSize: "14px", 
                                lineHeight: "1.5",
                                padding: "6px",
                                borderRadius: "4px",
                                resize: "vertical", // 开启右下角自由拖拽拉伸
                                overflowY: "auto"
                            });
                        }
                    });

                    this.updateDisplay = (index) => {
                        if (this.textsData && this.textsData.length > 0) {
                            textWidget.value = `[ 第 ${index + 1} 页 / 共 ${this.textsData.length} 页 ]\n-----------------------------------------\n${this.textsData[index]}`;
                        } else {
                            textWidget.value = "💡 节点就绪。等待运行...\n(若已连线，请点击右侧 Queue Prompt 触发数据)";
                        }
                        imgEl.src = (showImgWidget.value && this.imagesData && this.imagesData[index]) ? this.imagesData[index] : "";
                    };

                    this.updateDisplay(0);
                    
                    setTimeout(() => { 
                        this.setSize(this.computeSize());
                        this.onResize(this.size); 
                    }, 50);

                    return r;

                } catch (err) {
                    console.error("【翻页图文查看器】致命错误:", err);
                }
            };

            const onResize = nodeType.prototype.onResize;
            nodeType.prototype.onResize = function (size) {
                try {
                    if (onResize) onResize.apply(this, arguments);
                    const showImgWidget = this.widgets?.find(w => w.name === "显示对应图片 (Show Image)");
                    const isImgVisible = showImgWidget ? showImgWidget.value : false;

                    if (this.textWidget && this.textWidget.inputEl) {
                        // 空间计算回归简单直接，不再受列表干扰
                        let offset = isImgVisible ? 325 : 115;
                        let newHeight = Math.max(size[1] - offset, 60);
                        this.textWidget.inputEl.style.height = newHeight + "px";
                    }
                } catch (e) {}
            };

            nodeType.prototype.computeSize = function () {
                const showImgWidget = this.widgets?.find(w => w.name === "显示对应图片 (Show Image)");
                const isImgVisible = showImgWidget ? showImgWidget.value : false;
                return [400, isImgVisible ? 460 : 200];
            };

            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);
                
                if (message && message.texts && message.texts.length > 0) {
                    this.textsData = message.texts; 
                }
                
                this.imagesData = [];
                // ★ 核心修改：读取 Python 后端传来的 "custom_images"
                if (message && message.custom_images && message.custom_images.length > 0) {
                    this.imagesData = message.custom_images.map(img => {
                        return `/view?filename=${encodeURIComponent(img.filename)}&type=${img.type}&subfolder=${encodeURIComponent(img.subfolder)}`;
                    });
                }

                this.imgs = undefined; 
                
                const pWidget = this.widgets.find(w => w.name === "跳转页码 (Page)");
                if (pWidget && this.textsData) {
                    if (pWidget.options) pWidget.options.max = this.textsData.length;
                    pWidget.value = 1;
                }
                
                this.updateDisplay(0);
                this.setSize(this.computeSize());
                this.onResize(this.size);
                if (app.graph) app.graph.setDirtyCanvas(true, true);
            };
        }
    }
});