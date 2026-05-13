# MCP 완전 가이드 — 기초부터 심화까지

---

## 1단계 — MCP란 무엇인가?

### 정의
**MCP (Model Context Protocol)** 는 Anthropic이 설계한 **개방형 표준 프로토콜**입니다.
AI 모델(Claude 등)이 외부 도구·데이터·시스템과 **표준화된 방식**으로 통신할 수 있게 해줍니다.

### 왜 필요한가?

```
[ 기존 방식 ]
AI ──── 커스텀 코드 ────► 데이터베이스
AI ──── 또 다른 코드 ───► 파일시스템
AI ──── 또 다른 코드 ───► 외부 API
     (각각 따로 구현, 재사용 불가)

[ MCP 방식 ]
AI ──── MCP 표준 ────► MCP Server A (DB)
               └────► MCP Server B (파일)
               └────► MCP Server C (API)
     (하나의 규격으로 모두 연결)
```

> 한 마디로: **AI와 외부 세계를 잇는 USB 규격** 같은 것입니다.

---

## 2단계 — MCP 아키텍처

### 3개의 핵심 구성요소

```
┌─────────────────────────────────────────┐
│           MCP Host (Claude 등)          │
│  ┌──────────────┐                       │
│  │  MCP Client  │ ◄── AI가 탑재된 앱     │
│  └──────┬───────┘                       │
└─────────┼───────────────────────────────┘
          │  MCP Protocol (JSON-RPC 2.0)
          │
┌─────────▼───────────────────────────────┐
│           MCP Server                    │
│  ┌──────────┐ ┌─────────┐ ┌──────────┐  │
│  │  Tools   │ │Resources│ │ Prompts  │  │
│  └──────────┘ └─────────┘ └──────────┘  │
└─────────────────────────────────────────┘
```

| 구성요소 | 역할 |
|---------|------|
| **MCP Host** | Claude Desktop, Claude.ai, IDE 플러그인 등 AI를 실행하는 환경 |
| **MCP Client** | Host 안에서 MCP Server와 통신하는 클라이언트 모듈 |
| **MCP Server** | 실제 기능(도구, 데이터)을 제공하는 서버 프로세스 |

---

## 3단계 — MCP Server란?

### 개념
MCP Server는 AI에게 **특정 능력을 부여하는 독립 프로세스**입니다.
Python, Node.js 등으로 작성하며, AI가 요청하면 실행됩니다.

### 작동 방식

```
Claude: "현재 폴더의 파일 목록을 보여줘"
          │
          ▼
  [MCP Client가 서버로 요청 전송]
  {
    "method": "tools/call",
    "params": {
      "name": "list_files",
      "arguments": {"path": "./"}
    }
  }
          │
          ▼
  [MCP Server가 실제 실행 후 응답]
  {
    "content": [
      {"type": "text", "text": "main.py\nREADME.md\n..."}
    ]
  }
          │
          ▼
Claude: "현재 폴더에는 main.py, README.md 등이 있습니다."
```

### 전송 방식 (Transport)

| 방식 | 설명 | 사용 상황 |
|------|------|----------|
| **stdio** | 표준 입출력으로 통신 | 로컬 프로세스 (가장 일반적) |
| **HTTP+SSE** | HTTP 스트리밍 | 원격 서버, 웹 서비스 |
| **WebSocket** | 양방향 실시간 통신 | 실시간 데이터 필요 시 |

> 코드에서 `mcp.run(transport='stdio')` — 로컬 실행 방식을 사용하고 있습니다.

---

## 4단계 — MCP의 3대 기능

### ① Tools (도구) — AI가 **실행**할 수 있는 함수

```python
@mcp.tool()
def get_tia_status() -> str:
    """TIA Portal 상태를 반환합니다."""  # ← Claude가 이 설명을 보고 언제 쓸지 판단
    ...
```

- AI가 **능동적으로 호출**하는 함수
- 부작용(side effect) 있어도 됨 (파일 쓰기, API 호출 등)
- **Claude가 docstring을 읽고** 적절한 상황에 자동 선택

### ② Resources (리소스) — AI가 **읽을 수 있는** 데이터

```python
@mcp.resource("file://{path}")
def read_file(path: str) -> str:
    """파일 내용을 제공합니다."""
    with open(path) as f:
        return f.read()
```

- 데이터베이스, 파일, API 응답 등 **정적 데이터 노출**
- URI 형태로 식별 (`file://`, `db://`, `http://` 등)
- Tools보다 **부작용이 없는** 읽기 전용 데이터에 적합

### ③ Prompts (프롬프트) — **재사용 가능한** 프롬프트 템플릿

```python
@mcp.prompt()
def analyze_plc_block(block_name: str) -> str:
    return f"{block_name} 블록을 분석하고 개선점을 알려주세요."
```

- 자주 쓰는 프롬프트를 서버에서 관리
- 파라미터로 동적 생성 가능

---

## 5단계 — 작성하신 코드와 연결해서 보기

```python
# ▼ FastMCP: MCP 서버를 쉽게 만드는 Python 프레임워크
mcp = FastMCP("TIA_Portal_Openness")

# ▼ 이 서버가 제공하는 Tools 3개
@mcp.tool()  def get_tia_status()   # TIA 연결 상태 확인
@mcp.tool()  def list_plc_blocks()  # 블록 목록 조회
@mcp.tool()  def get_block_code()   # 블록 소스코드 추출

# ▼ stdio로 실행 → Claude Desktop 등에서 로컬 프로세스로 연동
mcp.run(transport='stdio')
```

**Claude가 이 서버를 쓰는 흐름:**
```
사용자: "현재 PLC의 모든 블록 목록 보여줘"
  │
  ▼
Claude가 판단: list_plc_blocks 툴이 적합하다
  │
  ▼
MCP Client → MCP Server(이 Python 파일) 호출
  │
  ▼
TIA Portal Openness API 실행
  │
  ▼
결과를 Claude에게 반환 → 사용자에게 답변
```

---

## 6단계 — 심화: MCP 통신 프로토콜

### JSON-RPC 2.0 기반

MCP는 내부적으로 **JSON-RPC 2.0** 규격을 씁니다.

```jsonc
// Client → Server: 툴 목록 요청
{ "jsonrpc": "2.0", "id": 1, "method": "tools/list" }

// Server → Client: 툴 목록 응답
{
  "jsonrpc": "2.0", "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_tia_status",
        "description": "TIA Portal에 연결하여 현재 상태를...",
        "inputSchema": { "type": "object", "properties": {} }
      }
    ]
  }
}
```

### 생명주기

```
1. Initialize  → 버전 협상, 기능 협의
2. Initialized → 준비 완료 알림
3. (반복) Request / Response / Notification
4. Shutdown    → 종료
```

---

## 7단계 — MCP 생태계 전체 그림

```
┌─────────────────────────────────────────────────┐
│                  사용자                          │
└───────────────────┬─────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│         MCP Host (Claude Desktop / IDE)         │
│                                                 │
│  Claude ──► MCP Client ──┬──► Server A (TIA)    │
│                          ├──► Server B (DB)     │
│                          ├──► Server C (Git)    │
│                          └──► Server D (Web)    │
└─────────────────────────────────────────────────┘
```

### 공개된 MCP 서버 예시들
| 서버 | 기능 |
|------|------|
| `filesystem` | 파일 읽기/쓰기 |
| `github` | PR, 이슈, 커밋 관리 |
| `postgres` | DB 쿼리 실행 |
| `brave-search` | 웹 검색 |
| **TIA Portal (이 코드)** | PLC 블록 조회/수정 |

---

## 정리

```
MCP
 ├── 역할: AI ↔ 외부 시스템 표준 연결 규격
 ├── MCP Server: 기능을 제공하는 독립 프로세스
 │    ├── Tools    → AI가 호출하는 함수
 │    ├── Resources → AI가 읽는 데이터
 │    └── Prompts  → 재사용 프롬프트
 └── 통신: JSON-RPC 2.0 (stdio / HTTP / WebSocket)
```