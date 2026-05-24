import re

class TagFilterDeduper:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tags_string": ("STRING", {"forceInput": True}),
                
                # ================= 1. Character (人物外貌) 模块 =================
                "enable_Character": ("BOOLEAN", {"default": False, "label_on": "人物外貌启用(ON)", "label_off": "人物外貌禁用(OFF)"}),
                "partial_Character": ("BOOLEAN", {"default": True, "label_on": "模糊匹配(Contains)", "label_off": "精确匹配(Exact)"}),
                "preset_Character": ("STRING", {"multiline": True, "default": "1girl, 1boy, hair, eyes, skin, ears, ponytail, twintails, braid, ahoge"}),
                
                # ================= 2. Style (画风画质) 模块 =================
                "enable_Style": ("BOOLEAN", {"default": False, "label_on": "画风画质启用(ON)", "label_off": "画风画质禁用(OFF)"}),
                "partial_Style": ("BOOLEAN", {"default": True, "label_on": "模糊匹配(Contains)", "label_off": "精确匹配(Exact)"}),
                "preset_Style": ("STRING", {"multiline": True, "default": "masterpiece, best quality, high quality, highres, absurdres, traditional media, sketch, watercolor, monochrome, comic, 3d, text, watermark"}),
                
                # ================= 3. Outfit (服装配饰) 模块 =================
                "enable_Outfit": ("BOOLEAN", {"default": False, "label_on": "服装配饰启用(ON)", "label_off": "服装配饰禁用(OFF)"}),
                "partial_Outfit": ("BOOLEAN", {"default": True, "label_on": "模糊匹配(Contains)", "label_off": "精确匹配(Exact)"}),
                "preset_Outfit": ("STRING", {"multiline": True, "default": "shirt, skirt, dress, pants, shorts, pantyhose, thighhighs, socks, shoes, jacket, hat, glasses, jewelry, gloves"}),
                
                # ================= 4. Custom (自定义/抽象玩法) 模块 =================
                "enable_Custom": ("BOOLEAN", {"default": False, "label_on": "自定义启用(ON)", "label_off": "自定义禁用(OFF)"}),
                "partial_Custom": ("BOOLEAN", {"default": True, "label_on": "模糊匹配(Contains)", "label_off": "精确匹配(Exact)"}),
                "preset_Custom": ("STRING", {"multiline": True, "default": ""}),

                # ================= 5. Purify Degrees (程度词提纯模块) =================
                "purify_degrees": ("BOOLEAN", {"default": False, "label_on": "开启提纯(Purify)", "label_off": "关闭提纯(Skip)"}),
                "purify_keywords": ("STRING", {"multiline": False, "default": ""}),
                "size_modifiers_preset": ("STRING", {
                    "multiline": True, 
                    "default": ""
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("filtered_tags (最终结果)", "removed_tags (被删词条)", "original_tags (去重后的原词)")
    FUNCTION = "process_tags"
    CATEGORY = "CustomTagging"

    def process_tags(self, tags_string, 
                     enable_Character, partial_Character, preset_Character,
                     enable_Style, partial_Style, preset_Style,
                     enable_Outfit, partial_Outfit, preset_Outfit,
                     enable_Custom, partial_Custom, preset_Custom,
                     purify_degrees, purify_keywords, size_modifiers_preset):
        
        # [新增] 标签标准化工具：统一小写、下划线转空格、剔除括号及括号内内容
        def normalize_tag(t):
            t = t.lower()
            t = t.replace('_', ' ')
            # 正则匹配并移除 " (xxx)" 这种格式的内容
            t = re.sub(r'\s*\([^)]*\)', '', t)
            return t.strip()

        # [修改] 解析配置框输入时，直接将词库全部标准化处理
        def parse_to_normalized_set(text):
            return {normalize_tag(t) for t in text.replace('\n', ',').split(',') if t.strip()}

        char_bl = parse_to_normalized_set(preset_Character) if enable_Character else set()
        style_bl = parse_to_normalized_set(preset_Style) if enable_Style else set()
        outfit_bl = parse_to_normalized_set(preset_Outfit) if enable_Outfit else set()
        custom_bl = parse_to_normalized_set(preset_Custom) if enable_Custom else set()

        raw_tags = [tag.strip() for tag in tags_string.split(",")]
        unique_tags = list(dict.fromkeys(raw_tags))
        
        base_filtered = []
        removed_tags = [] 

        def is_match(norm_tag, bl_set, is_partial):
            if not bl_set: return False
            if is_partial:
                for bl_term in bl_set:
                    if bl_term in norm_tag: return True
                return False
            else:
                return norm_tag in bl_set

        # ================= 第一阶段：基础模块过滤 =================
        for tag in unique_tags:
            if not tag: continue
            
            # 提取标准化后的词用于比对，但操作和保存依然用原词 `tag`
            norm_tag = normalize_tag(tag)
            
            hit = (is_match(norm_tag, char_bl, partial_Character) or
                   is_match(norm_tag, style_bl, partial_Style) or
                   is_match(norm_tag, outfit_bl, partial_Outfit) or
                   is_match(norm_tag, custom_bl, partial_Custom))

            if hit:
                removed_tags.append(tag)
            else:
                base_filtered.append(tag)

        # ================= 第二阶段：尺寸提纯模块 =================
        final_tags = base_filtered.copy()
        if purify_degrees:
            p_keywords = [normalize_tag(k) for k in purify_keywords.split(",") if k.strip()]
            size_modifiers = parse_to_normalized_set(size_modifiers_preset)
            
            to_remove = set()
            for keyword in p_keywords:
                # 找出所有包含该主体词的标签（基于标准化文本）
                matched_tags = [t for t in base_filtered if keyword in normalize_tag(t)]
                
                if len(matched_tags) > 1:
                    for i in range(len(matched_tags)):
                        norm_tag_i = normalize_tag(matched_tags[i])
                        
                        # 场景 A: 存在基础词，且存在修饰词组合 ，删去基础词
                        if norm_tag_i == keyword:
                            for other_tag in matched_tags:
                                norm_other_tag = normalize_tag(other_tag)
                                if norm_other_tag != keyword:
                                    prefix = norm_other_tag.replace(keyword, "").strip()
                                    if prefix in size_modifiers:
                                        to_remove.add(matched_tags[i]) # 添加原词到待删除列表
                                        break
                            continue
                        
                        # 场景 B: 存在两个包含修饰词的组合词 
                        for j in range(len(matched_tags)):
                            if i == j: continue
                            norm_tag_j = normalize_tag(matched_tags[j])
                            
                            # 后缀匹配主体词，并提取修饰前缀比对
                            if len(norm_tag_j) > len(norm_tag_i) and norm_tag_j.endswith(keyword) and norm_tag_i.endswith(keyword):
                                prefix_i = norm_tag_i.replace(keyword, "").strip()
                                prefix_j = norm_tag_j.replace(keyword, "").strip()
                                
                                # 如果前缀都在尺寸修饰库里，删去较短的那个（低层级）
                                if prefix_i in size_modifiers and prefix_j in size_modifiers:
                                    to_remove.add(matched_tags[i])

            for r_tag in to_remove:
                if r_tag in final_tags:
                    final_tags.remove(r_tag)
                    removed_tags.append(f"[尺寸提纯]{r_tag}")

        filtered_str = ", ".join(final_tags)
        removed_str = ", ".join(removed_tags)
        original_str = ", ".join(unique_tags)

        return (filtered_str, removed_str, original_str)

NODE_CLASS_MAPPINGS = {"TagFilterDeduper": TagFilterDeduper}
NODE_DISPLAY_NAME_MAPPINGS = {"TagFilterDeduper": "🔧 自定义TAG去重过滤 (Custom Tag Filter)"}
