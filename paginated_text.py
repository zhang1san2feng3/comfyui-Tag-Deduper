import os
import torch
import folder_paths
from PIL import Image
import numpy as np
import random
import string

class PaginatedTextViewer:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "texts": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "images": ("IMAGE",),
            },
            "hidden": {"unique_id": "UNIQUE_ID", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ()
    FUNCTION = "display_text"
    OUTPUT_NODE = True
    CATEGORY = "CustomTagging"

    def display_text(self, texts, images=None, unique_id=None, extra_pnginfo=None):
        # 1. 展平文本列表
        flat_texts = []
        for t in texts:
            if isinstance(t, list):
                flat_texts.extend(t)
            else:
                flat_texts.append(t)
                
        # 2. 在后端直接处理图片
        ui_images = []
        if images is not None:
            temp_dir = folder_paths.get_temp_directory()
            for img_tensor in images:
                if len(img_tensor.shape) == 4:
                    for i in range(img_tensor.shape[0]):
                        ui_images.append(self._save_temp_image(img_tensor[i], temp_dir))
                else:
                    ui_images.append(self._save_temp_image(img_tensor, temp_dir))

        # ★ 核心修改：将 "images" 改为 "custom_images"，防止 ComfyUI 自动生成原生图片列表
        return {"ui": {"texts": flat_texts, "custom_images": ui_images}, "result": ()}

    def _save_temp_image(self, tensor, temp_dir):
        img_np = 255.0 * tensor.cpu().numpy()
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)
        pil_img = Image.fromarray(img_np)
        
        rand_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        filename = f"viewer_{rand_str}.png"
        
        filepath = os.path.join(temp_dir, filename)
        pil_img.save(filepath, compress_level=1)
        
        return {
            "filename": filename,
            "type": "temp",
            "subfolder": ""
        }

NODE_CLASS_MAPPINGS = {"PaginatedTextViewer": PaginatedTextViewer}
NODE_DISPLAY_NAME_MAPPINGS = {"PaginatedTextViewer": "📖 翻页图文查看器 (Paginated Prompt Viewer)"}