"""
Sandbox File Tree - Docker container dosya gezgini
"""
from textual.widgets import Tree
from textual.widgets.tree import TreeNode
from rich.text import Text
import json
import os

from tools.sandbox import sandbox_list_files
from utils.logger import get_logger

logger = get_logger()

class SandboxTree(Tree):
    """Docker container içindeki dosyaları gösteren ağaç yapısı"""
    
    def __init__(self, path: str = "/home/agent", **kwargs):
        super().__init__("🐳 Sandbox Home", data="/home/agent", **kwargs)
        self.root.expand()
        
    def on_mount(self) -> None:
        self._load_directory(self.root, "/home/agent")
        
    def _load_directory(self, node: TreeNode, path: str):
        """Dizini yükle ve node'a ekle"""
        try:
            # Backend'den dosyaları al
            result = sandbox_list_files.invoke({"path": path})
            items = json.loads(result)
            
            # Klasörleri önce, dosyaları sonra sırala
            items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
            
            for item in items:
                name = item["name"]
                full_path = item["path"]
                is_dir = item["is_dir"]
                
                if is_dir:
                    # Klasör
                    label = Text(f"📁 {name}", style="bold yellow")
                    child = node.add(label, data=full_path, expand=False)
                    # Boş bir dummy node ekle ki genişletilebilir görünsün
                    child.add("Loading...", data=None)
                else:
                    # Dosya
                    icon = self._get_icon(name)
                    size_str = self._format_size(item.get("size", 0))
                    label = Text(f"{icon} {name} ", style="white")
                    label.append(f"({size_str})", style="dim")
                    node.add_leaf(label, data=full_path)
                    
        except Exception as e:
            logger.error(f"SandboxTree load error: {e}")
            node.add_leaf(f"Error: {e}")

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        """Klasör genişletildiğinde içeriğini yükle"""
        node = event.node
        path = node.data
        
        if not path or node.is_root:
            return
            
        # Eğer zaten yüklendiyse (dummy node yoksa) tekrar yükleme
        # Label bir Text objesi olabilir, string'e çevir
        if len(node.children) == 1:
            child_label = str(node.children[0].label)
            if "Loading" in child_label:
                node.remove_children()
                self._load_directory(node, path)

    def _get_icon(self, filename: str) -> str:
        """Dosya uzantısına göre ikon döndür"""
        ext = os.path.splitext(filename)[1].lower()
        icons = {
            ".py": "🐍",
            ".js": "📜",
            ".html": "🌐",
            ".css": "🎨",
            ".json": "{}",
            ".md": "📝",
            ".txt": "📄",
            ".sh": "🐚",
            ".dockerfile": "🐳",
            ".yml": "⚙️",
            ".yaml": "⚙️"
        }
        return icons.get(ext, "📄")

    def _format_size(self, size: int) -> str:
        """Dosya boyutunu formatla"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
