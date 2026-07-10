import tree_sitter
from typing import Dict, Any, Optional
from ai.utils.logger import get_logger

logger = get_logger("parsers.ast")

class ASTParser:
    """Reusable AST utilities using Tree-sitter for multiple languages."""
    
    def __init__(self):
        self.parsers: Dict[str, tree_sitter.Parser] = {}
        self.languages: Dict[str, tree_sitter.Language] = {}
        # Pre-initialize common languages if the bindings are installed
        self._try_load_language("python", "tree_sitter_python")
        self._try_load_language("java", "tree_sitter_java")
        self._try_load_language("javascript", "tree_sitter_javascript")
        self._try_load_language("typescript", "tree_sitter_typescript")
        self._try_load_language("go", "tree_sitter_go")
        self._try_load_language("rust", "tree_sitter_rust")
        self._try_load_language("cpp", "tree_sitter_cpp")
        self._try_load_language("c_sharp", "tree_sitter_c_sharp")
        self._try_load_language("php", "tree_sitter_php")

    def _try_load_language(self, lang_name: str, module_name: str):
        try:
            import importlib
            module = importlib.import_module(module_name)
            # In tree-sitter v0.22+, language modules provide a language() method
            lang = tree_sitter.Language(module.language())
            parser = tree_sitter.Parser()
            parser.set_language(lang)
            self.languages[lang_name] = lang
            self.parsers[lang_name] = parser
        except (ImportError, AttributeError, Exception) as e:
            logger.debug(f"Failed to load tree-sitter language binding for {lang_name}: {e}")

    def parse(self, code: bytes, lang_name: str) -> Optional[tree_sitter.Tree]:
        """Parses the given code into an AST for the specified language."""
        if lang_name not in self.parsers:
            logger.warning(f"No parser loaded for language: {lang_name}")
            return None
        return self.parsers[lang_name].parse(code)
        
    def find_nodes(self, node: tree_sitter.Node, node_type: str) -> list[tree_sitter.Node]:
        """Recursively find all nodes of a specific type in the AST."""
        results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            results.extend(self.find_nodes(child, node_type))
        return results

    def extract_function_definitions(self, root_node: tree_sitter.Node, lang_name: str) -> list[tree_sitter.Node]:
        """Extract function/method definitions based on the language."""
        types_map = {
            "python": ["function_definition"],
            "java": ["method_declaration"],
            "javascript": ["function_declaration", "arrow_function"],
            "typescript": ["function_declaration", "arrow_function", "method_definition"],
            "go": ["function_declaration", "method_declaration"],
            "rust": ["function_item"],
            "cpp": ["function_definition"],
            "c_sharp": ["method_declaration"],
            "php": ["function_definition", "method_declaration"]
        }
        target_types = types_map.get(lang_name, [])
        results = []
        for t in target_types:
            results.extend(self.find_nodes(root_node, t))
        return results

ast_parser = ASTParser()
