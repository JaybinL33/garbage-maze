*This project has been created as part of the 42 curriculum by jungblee, hyunlee.*

# A-Maze-ing

## Description

설정 파일을 읽어 미로를 만들고, 벽과 최단 경로를 파일에 저장한 뒤
MiniLibX 창으로 보여주는 Python 프로젝트입니다. 생성기 `mazegen`은
화면이나 파일 저장 기능 없이 다른 프로젝트에서도 사용할 수 있습니다.

- `PERFECT=False`: 기본 모드입니다. 순환 경로를 만들고 막다른길을 줄입니다.
- `PERFECT=True`: 순환 없이, 이동 가능한 두 칸 사이의 경로가 하나인 미로를 만듭니다.

## Instructions

### 설치와 실행

Ubuntu x86-64, Python 3.10 이상, `make`, [uv][uv-install]가 필요합니다.
화면을 띄우려면 X11 환경과 Vulkan 드라이버가 필요하며, Wayland에서는
XWayland를 사용합니다. 시스템 라이브러리는 XCB, XCB keysyms, Vulkan,
zlib, libbsd가 필요합니다.

저장소 루트에서 실행합니다.

~~~sh
make install
make run
~~~

`make install`은 `uv.lock`에 맞춰 `.venv`와 Python 의존성을 준비합니다.
MLX는 동봉한 Ubuntu wheel을 사용합니다. 시스템 라이브러리와 드라이버는
따로 설치해야 합니다.

직접 실행하거나 다른 설정 파일을 사용하려면:

~~~sh
source .venv/bin/activate
python3 a_maze_ing.py config.txt
~~~

`config.txt` 자리에 사용할 파일 경로를 넣습니다. 인자는 이 파일 하나입니다.
실행하면 `OUTPUT_FILE`에 미로가 저장되고 창이 열립니다.
같은 파일이 이미 있으면 덮어씁니다.

### 조작과 개발 명령

| 키 | 동작 |
| --- | --- |
| `R` | 새 미로를 생성·저장하고 화면 갱신 |
| `P` | 최단 경로 표시·숨김 |
| `C` | 벽 색상 전환 |
| `Escape` / 창 닫기 | 종료 |

시작점은 청록색, 끝점은 산호색, 경로는 호박색, `42` 문양은 보라색입니다.
셀 간격은 16픽셀로 고정되어 있어 큰 미로는 화면 밖으로 잘릴 수 있습니다.

| 명령 | 동작 |
| --- | --- |
| `make debug` | Python 디버거 `pdb`로 실행 |
| `make lint` | flake8와 과제 지정 옵션의 mypy 검사 |
| `make lint-strict` | flake8와 mypy strict 검사 |
| `make package` | 소스에서 루트의 제출용 wheel 다시 빌드 |
| `make clean` | Python·mypy 캐시와 빌드 중간 파일 삭제 |

`make clean`은 가상환경, 출력 미로, 제출용 wheel을 보존합니다.

## 설정 파일

기본 [config.txt](config.txt)는 다음과 같습니다.

~~~ini
WIDTH=25
HEIGHT=17
ENTRY=0,0
EXIT=24,16
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=42
~~~

| 키 | 필수 | 값 |
| --- | --- | --- |
| `WIDTH`, `HEIGHT` | 예 | 양의 정수인 가로·세로 칸 수 |
| `ENTRY`, `EXIT` | 예 | 서로 다른 시작·끝 좌표 `x,y` |
| `OUTPUT_FILE` | 예 | 저장할 파일 경로 |
| `PERFECT` | 예 | 정확히 `True` 또는 `False` |
| `SEED` | 아니요 | 재현에 사용할 정수 |

좌표는 왼쪽 위 `(0, 0)`에서 시작하며, 오른쪽으로 x, 아래쪽으로 y가 증가합니다.
시작과 끝은 미로 안에 있어야 하고, 중앙의 닫힌 `42` 칸과 겹칠 수 없습니다.
기본 모드는 순환을 두 개 만들 수 없는 `(WIDTH - 1) * (HEIGHT - 1) < 2`인
크기를 거부합니다. `42`를 배치하기에 작으면 오류 메시지를 출력하고 문양 없이 생성합니다.

한 줄에 `KEY=VALUE` 하나를 씁니다. 빈 줄과 `#`로 시작하는 주석 줄은 무시합니다.
키와 값 양쪽의 공백은 허용하며, 키 이름은 대소문자를 구분합니다.
지원하지 않는 키는 오류이고, 중복 키는 마지막 값을 사용합니다.
줄 끝 주석은 지원하지 않습니다. 상대 파일 경로는 실행한 폴더를 기준으로 합니다.

`SEED`를 생략하면 실행할 때 새 난수 흐름을 만듭니다. 지정하면 같은 설정과
같은 Python·코드 환경에서 생성 순서를 재현할 수 있습니다. `R`은 시드를 다시
설정하지 않고 그 흐름을 이어갑니다. 값이 비어 있거나 정수가 아니면 오류입니다.

## 생성 방식

**무작위 깊이 우선 탐색(DFS)**으로 방문하지 않은 이웃을 연결합니다.
더 갈 곳이 없으면 되돌아가 다른 이웃을 찾습니다. 재귀 대신 스택을 사용하므로
큰 미로에서도 재귀 깊이 제한을 받지 않습니다.

이 단계의 결과는 모든 통로가 연결된 트리이며, perfect 모드는 여기서 끝납니다.
기본 모드에서는 막다른길의 벽을 추가로 열어 최소 두 개의 독립 순환을 만듭니다.
이후 **너비 우선 탐색(BFS)**으로 시작부터 끝까지의 최단 경로를 구합니다.

DFS는 전체 간선 목록이나 별도의 집합 관리 구조 없이 격자와 스택만으로
구현할 수 있어 선택했습니다. 생성과 경로 탐색에 필요한 시간·메모리는
칸 수에 비례합니다. 생성 로직은 `mazegen/`, 설정·저장·화면 처리는
`a_maze_ing.py`가 맡습니다.

## 출력 파일

한 칸을 16진수 한 자리로 저장합니다. 벽의 비트값은 북 `1`, 동 `2`, 남 `4`,
서 `8`이며, **1이면 벽, 0이면 통로**입니다. 예를 들어 `A`는 동·서쪽이 막힌 칸입니다.

미로를 행마다 한 줄씩 쓴 뒤, 빈 줄과 시작 좌표·끝 좌표·최단 경로를 씁니다.
경로는 `N`, `E`, `S`, `W`로 나타내며 모든 줄은 줄바꿈으로 끝납니다.
가로 두 칸짜리 perfect 미로의 출력 예시입니다.

~~~text
D7

0,0
1,0
E
~~~

## 생성기 재사용

루트의 `mazegen-1.0.0-py3-none-any.whl`에는 생성기와 사용 설명이 들어 있습니다.
MLX나 이미지 에셋은 필요하지 않습니다. 다른 프로젝트의 가상환경에서
wheel 파일을 복사한 위치로 이동한 뒤 설치합니다.

~~~sh
python3 -m pip install ./mazegen-1.0.0-py3-none-any.whl
~~~

~~~python
from random import Random

from mazegen import MazeGenerator

rng = Random(42)
maze = MazeGenerator(25, 17, (0, 0), (24, 16), rng=rng, perfect=False)

print(maze.walls[0][0])
print(maze.entry, maze.exit)
print(maze.path)
~~~

앞의 네 인자는 가로·세로 크기와 시작·끝 좌표입니다. `rng`는 필수이고,
`perfect`는 생략하면 `False`입니다. 같은 `rng`를 다음 생성에도 전달하면
난수 흐름이 이어집니다.

`walls[y][x]`는 위에서 설명한 벽 코드입니다. `path`는 시작과 끝을 포함한
`(x, y)` 좌표들로 이루어진 튜플입니다.
자세한 API는 [패키지 사용 설명](mazegen/README.md)에 있습니다.

## 팀과 진행 방식

- `hyunlee`: 미로 생성·최단 경로 탐색과 생성기 API.
- `jungblee`: 설정·파일 출력·MLX 화면과 패키징.

처음에는 벽과 경로의 전달 형식을 정하고, 생성기와 앱을 나누어 구현한 뒤
통합하는 순서를 계획했습니다. 이후 알고리즘과 화면 구성을 비교하면서,
현재 제출본은 생성기 패키지와 앱 한 파일을 중심으로 단순화했습니다.

잘된 점은 벽과 좌표라는 작은 인터페이스 덕분에 생성기와 화면을 따로
검사할 수 있었다는 것입니다. 개선할 점은 구현 전에 요구사항을 더 정확히
정리하는 것입니다. 시드의 재현 방식과 작은 미로의 `42` 배치 조건을 뒤늦게 재검토했습니다.

버전 관리는 Jujutsu/Git, 환경 구성은 uv, 패키징은 setuptools를 사용합니다.
코드는 flake8·mypy로, 동작은 별도 테스트와 과제 제공 분석기로 확인합니다.

## Resources

- [A-Maze-ing v2.3 과제 원문][subject]과 함께 제공된 `maze_analyzer.py`.
- [MIT DFS 강의][dfs], [MIT BFS 강의][bfs] — 그래프 탐색의 원리.
- [Python random][random] — 시드와 난수 객체.
- [MiniLibX 문서 위치와 Python API 안내](third_party/mlx/README.md).
- [uv 프로젝트 사용법][uv-project], [Python 패키징 가이드][packaging].

AI는 요구사항 해석과 알고리즘 비교, `mazegen`·`a_maze_ing.py`의 초안 및
리팩터링, 테스트 작성, 패키징 점검과 문서 작성에 사용했습니다.

## 라이선스

프로젝트 코드는 [Blue Oak Model License 1.0.0](LICENSE.md),
동봉한 MiniLibX는 [별도의 MIT 라이선스](third_party/mlx/LICENSE.md)를 따릅니다.

[subject]: https://cdn.intra.42.fr/pdf/pdf/224851/en.subject.pdf
[uv-install]: https://docs.astral.sh/uv/getting-started/installation/
[uv-project]: https://docs.astral.sh/uv/guides/projects/
[packaging]: https://packaging.python.org/en/latest/tutorials/packaging-projects/
[random]: https://docs.python.org/3/library/random.html
[dfs]: https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/lecture-14-depth-first-search-dfs-topological-sort/
[bfs]: https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/lecture-13-breadth-first-search-bfs/
