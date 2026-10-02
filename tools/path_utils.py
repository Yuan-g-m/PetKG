import os

# 获取项目根目录
project_root = os.path.dirname(os.path.dirname(__file__))


def resolve_from_project_root(relative_path) -> str:
    """将相对路径基于项目根目录拼接为绝对路径"""
    return str(os.path.join(project_root, relative_path))


if __name__ == "__main__":
    print(resolve_from_project_root("cookie_dir/"))
