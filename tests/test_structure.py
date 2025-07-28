# 基础测试文件
from pathlib import Path

def test_project_structure():
    """测试项目结构是否正确"""
    project_root = Path(__file__).parent.parent
    
    # 检查核心目录
    assert (project_root / "src" / "pdftranslate_web").exists()
    assert (project_root / "scripts").exists()
    assert (project_root / "docs").exists()
    
    # 检查核心文件
    assert (project_root / "src" / "pdftranslate_web" / "__init__.py").exists()
    assert (project_root / "src" / "pdftranslate_web" / "api_server.py").exists()
    assert (project_root / "src" / "pdftranslate_web" / "api_client.py").exists()
    assert (project_root / "src" / "pdftranslate_web" / "gradio_client.py").exists()
    
    # 检查配置文件
    assert (project_root / ".env.example").exists()
    assert (project_root / "pyproject.toml").exists()
    assert (project_root / "README.md").exists()
    
    # 检查Docker文件
    assert (project_root / "Dockerfile").exists()
    assert (project_root / "docker-compose.yml").exists()

if __name__ == "__main__":
    test_project_structure()
    print("✅ 项目结构测试通过")