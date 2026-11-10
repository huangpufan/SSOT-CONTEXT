"""Independent task inputs for generic-context trials; no model calls."""
import importlib.util
from pathlib import Path
import scenarios
import source_cases

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("continuity", HERE.parent / "continuity_cases.py")
continuity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(continuity)
CASES = ("C01", "D03", *scenarios.CASES, "C06", "C07")

MATERIAL = {
    "SPACE.md": """# 一个可持续的生活空间

这个空间连接我的开发、人生、研究、创作和团队工作；它自己的目标是每周留出十小时不被项目挤占的自由时间。

## 跨域关系与边界

研究为创作提供资料，不能把待验证的研究结论直接变成作品 canon。团队项目使用公司的资料，个人创作只有取得授权才能引用。开发排期和团队排期共享精力预算，任何一方不能替另一方作承诺。

## 当前安排

2026-11-10：本月每周三晚留给写作，这是本月安排，不是终身偏好。
""",
    "development/notes.md": "# 开发\n\n个人维护一个离线记事工具；技术选择尚未确定。\n",
    "life/notes.md": "# 人生\n\n最近搬家，想慢慢适应新街区；这是当前经历，不是人格判断。\n",
    "research/notes.md": "# 研究\n\n在阅读城市夜间交通资料，结论仍待来源核对。\n",
    "creation/notes.md": "# 创作\n\n一部短篇处于草稿阶段；角色声称知道的事不自动成为 canon。\n",
    "team/notes.md": "# 团队\n\n团队资料归公司所有；当前没有把它复制进个人作品的授权。\n",
}

TASK = """这里是我的长期生活与工作空间，不是软件仓库，没有 Git。我同意为它建立 SSOT 记忆入口，并在当前空间内保存必要的记忆。现有 SPACE.md 是顶层目标、跨域关系和边界的权威 owner，各领域 notes.md 继续各自持有原内容。请建立一个下一位协作者可直接使用的简洁入口，既能理解空间自身，也能找到开发、人生、研究、创作和团队的相关内容。保持原件和 owner 路径，完成后读回实际保存的入口并说明可继续使用的范围。"""


def build(repo, case):
    if case in ("C06", "C07"):
        source_cases.build(repo, scenarios.write, interrupted=case == "C07")
        return None
    if case == "D03":
        return continuity.fixture(repo, "partial")
    if case != "C01":
        return scenarios.build(repo, case, continuity)
    repo.mkdir(parents=True)
    for name, body in MATERIAL.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    return None


def tasks(case):
    if case in ("C06", "C07"):
        return source_cases.tasks(case)
    if case == "C01":
        return [TASK]
    return continuity.tasks("partial") if case == "D03" else scenarios.tasks(case)


def before_turn(repo, case, turn):
    if case in ("C06", "C07"):
        return source_cases.before_turn(repo, case, turn, scenarios.write)
    scenarios.before_turn(repo, case, turn)
