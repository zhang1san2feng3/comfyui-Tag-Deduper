from .tag_deduper import NODE_CLASS_MAPPINGS as td_nodes, NODE_DISPLAY_NAME_MAPPINGS as td_names
from .paginated_text import NODE_CLASS_MAPPINGS as pg_nodes, NODE_DISPLAY_NAME_MAPPINGS as pg_names

# 合并两个节点的注册信息
NODE_CLASS_MAPPINGS = {**td_nodes, **pg_nodes}
NODE_DISPLAY_NAME_MAPPINGS = {**td_names, **pg_names}

# 注册 web 目录，确保前端 JS 生效
WEB_DIRECTORY = "./web/js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]