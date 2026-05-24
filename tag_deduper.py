class TagFilterDeduper:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tags_string": ("STRING", {"forceInput": True}),
                
                # ================= 1. Character (人物外貌) 模块 =================
                "enable_Character": ("BOOLEAN", {"default": False, "label_on": "启用(ON)", "label_off": "禁用(OFF)"}),
                "partial_Character": ("BOOLEAN", {"default": True, "label_on": "模糊匹配(Contains)", "label_off": "精确匹配(Exact)"}),
                "preset_Character": ("STRING", {"multiline": True, "default": "1girl, 1boy, hair, eyes, skin, ears, ponytail, twintails, braid, ahoge"}),
                
                # ================= 2. Style (画风画质) 模块 =================
                "enable_Style": ("BOOLEAN", {"default": False, "label_on": "启用(ON)", "label_off": "禁用(OFF)"}),
                "partial_Style": ("BOOLEAN", {"default": True, "label_on": "模糊匹配(Contains)", "label_off": "精确匹配(Exact)"}),
                "preset_Style": ("STRING", {"multiline": True, "default": "masterpiece, best quality, high quality, highres, absurdres, traditional media, sketch, watercolor, monochrome, comic, 3d, text, watermark"}),
                
                # ================= 3. Outfit (服装配饰) 模块 =================
                "enable_Outfit": ("BOOLEAN", {"default": False, "label_on": "启用(ON)", "label_off": "禁用(OFF)"}),
                "partial_Outfit": ("BOOLEAN", {"default": True, "label_on": "模糊匹配(Contains)", "label_off": "精确匹配(Exact)"}),
                "preset_Outfit": ("STRING", {"multiline": True, "default": "shirt, skirt, dress, pants, shorts, pantyhose, thighhighs, socks, shoes, jacket, hat, glasses, jewelry, gloves"}),
                
                # ================= 4. Custom (自定义/抽象玩法) 模块 =================
                # 修复：默认改为 False，与整体保持一致
                "enable_Custom": ("BOOLEAN", {"default": False, "label_on": "启用(ON)", "label_off": "禁用(OFF)"}),
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
        
        def parse_to_set(text):
            return {t.strip().lower() for t in text.replace('\n', ',').split(',') if t.strip()}

        char_bl = parse_to_set(preset_Character) if enable_Character else set()
        style_bl = parse_to_set(preset_Style) if enable_Style else set()
        outfit_bl = parse_to_set(preset_Outfit) if enable_Outfit else set()
        custom_bl = parse_to_set(preset_Custom) if enable_Custom else set()

        raw_tags = [tag.strip() for tag in tags_string.split(",")]
        unique_tags = list(dict.fromkeys(raw_tags))
        
        base_filtered = []
        removed_tags = [] 

        def is_match(tag_lower, bl_set, is_partial):
            if not bl_set: return False
            if is_partial:
                for bl_term in bl_set:
                    if bl_term in tag_lower: return True
                return False
            else:
                return tag_lower in bl_set

        for tag in unique_tags:
            if not tag: continue
            tag_lower = tag.lower()
            
            hit = (is_match(tag_lower, char_bl, partial_Character) or
                   is_match(tag_lower, style_bl, partial_Style) or
                   is_match(tag_lower, outfit_bl, partial_Outfit) or
                   is_match(tag_lower, custom_bl, partial_Custom))

            if hit:
                removed_tags.append(tag)
            else:
                base_filtered.append(tag)

        final_tags = base_filtered.copy()
        if purify_degrees:
            p_keywords = [k.strip().lower() for k in purify_keywords.split(",") if k.strip()]
            size_modifiers = parse_to_set(size_modifiers_preset)
            
            to_remove = set()
            for keyword in p_keywords:
                matched_tags = [t for t in base_filtered if keyword in t.lower()]
                if len(matched_tags) > 1:
                    for i in range(len(matched_tags)):
                        tag_i = matched_tags[i].lower()
                        if tag_i == keyword:
                            for other_tag in matched_tags:
                                other_tag_lower = other_tag.lower()
                                if other_tag_lower != keyword:
                                    prefix = other_tag_lower.replace(keyword, "").strip()
                                    if prefix in size_modifiers:
                                        to_remove.add(matched_tags[i])
                                        break
                            continue
                        
                        for j in range(len(matched_tags)):
                            if i == j: continue
                            tag_j = matched_tags[j].lower()
                            if len(tag_j) > len(tag_i) and tag_j.endswith(keyword) and tag_i.endswith(keyword):
                                prefix_i = tag_i.replace(keyword, "").strip()
                                prefix_j = tag_j.replace(keyword, "").strip()
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