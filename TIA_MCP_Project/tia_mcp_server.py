#Python

from mcp.server.fastmcp import FastMCP
import sys
import clr
import tempfile
import os

mcp = FastMCP("TIA_Portal_Openness")

TIA_BIN = r"C:\Program Files\Siemens\Automation\Portal V20\Bin"
TIA_API = r"C:\Program Files\Siemens\Automation\Portal V20\PublicAPI\V20\Siemens.Engineering.dll"


def _setup_tia():
    if TIA_BIN not in sys.path:
        sys.path.append(TIA_BIN)
    clr.AddReference(TIA_API)
    import Siemens.Engineering as tia
    return tia


def _get_plc_software(project):
    from Siemens.Engineering.HW.Features import SoftwareContainer
    for device in project.Devices:
        for device_item in device.DeviceItems:
            container = device_item.GetService[SoftwareContainer]()
            if container is not None:
                return container.Software
    raise RuntimeError("PLC 소프트웨어를 찾을 수 없습니다.")


def _find_block(block_group, block_name: str):
    for block in block_group.Blocks:
        if block.Name == block_name:
            return block
    for group in block_group.Groups:
        result = _find_block(group, block_name)
        if result is not None:
            return result
    return None


def _collect_blocks(block_group, result: list, prefix: str = ""):
    for block in block_group.Blocks:
        result.append(f"{prefix}{block.Name} [{block.GetType().Name}]")
    for group in block_group.Groups:
        result.append(f"{prefix}[그룹] {group.Name}")
        _collect_blocks(group, result, prefix + "  ")


@mcp.tool()
def get_tia_status() -> str:
    """TIA Portal에 연결하여 현재 상태와 열려있는 프로젝트 이름을 반환합니다."""
    try:
        tia = _setup_tia()
        processes = tia.TiaPortal.GetProcesses()
        if processes.Count > 0:
            portal = processes[0].Attach()
            if portal.Projects.Count > 0:
                return f"[성공] 현재 연결된 프로젝트: {portal.Projects[0].Name}"
            return "[성공] TIA Portal에 연결되었으나, 열려있는 프로젝트가 없습니다."
        return "[실패] 실행 중인 TIA Portal 프로세스를 찾을 수 없습니다."
    except Exception as e:
        return f"[오류] 연결 중 문제 발생: {str(e)}"


@mcp.tool()
def list_plc_blocks() -> str:
    """TIA Portal 프로젝트의 모든 PLC 블록 목록을 반환합니다."""
    try:
        tia = _setup_tia()
        processes = tia.TiaPortal.GetProcesses()
        if processes.Count == 0:
            return "[실패] 실행 중인 TIA Portal 프로세스를 찾을 수 없습니다."

        portal = processes[0].Attach()
        if portal.Projects.Count == 0:
            return "[실패] 열려있는 프로젝트가 없습니다."

        project = portal.Projects[0]
        plc_software = _get_plc_software(project)

        blocks = []
        _collect_blocks(plc_software.BlockGroup, blocks)

        if not blocks:
            return "[결과] 블록이 없습니다."
        return f"[성공] '{project.Name}' 블록 목록:\n" + "\n".join(blocks)
    except Exception as e:
        return f"[오류] {str(e)}"


@mcp.tool()
def get_block_code(block_name: str) -> str:
    """TIA Portal에서 지정한 블록의 소스 코드를 반환합니다."""
    import System

    try:
        tia = _setup_tia()
        processes = tia.TiaPortal.GetProcesses()
        if processes.Count == 0:
            return "[실패] 실행 중인 TIA Portal 프로세스를 찾을 수 없습니다."

        portal = processes[0].Attach()
        if portal.Projects.Count == 0:
            return "[실패] 열려있는 프로젝트가 없습니다."

        project = portal.Projects[0]
        plc_software = _get_plc_software(project)

        block = _find_block(plc_software.BlockGroup, block_name)
        if block is None:
            return f"[실패] '{block_name}' 블록을 찾을 수 없습니다."

        with tempfile.TemporaryDirectory() as tmp_dir:
            export_path = os.path.join(tmp_dir, f"{block_name}.xml")
            export_options = getattr(tia.ExportOptions, 'None')
            block.Export(System.IO.FileInfo(export_path), export_options)

            with open(export_path, 'r', encoding='utf-8') as f:
                content = f.read()

        return f"[성공] '{block_name}' 블록 소스 코드:\n\n{content}"
    except Exception as e:
        return f"[오류] {str(e)}"


if __name__ == "__main__":
    mcp.run(transport='stdio')
