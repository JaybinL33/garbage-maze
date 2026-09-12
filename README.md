*This project has been created as part of the 42 curriculum by jungblee, hyunlee.*

# A-Maze-ing

## Description

설정 파일로 미로를 만들고, 과제의 16진수 형식으로 저장한 뒤 MiniLibX로
표시합니다. 생성기 `mazegen`은 파일이나 그래픽 없이 별도로 재사용할 수 있습니다.

- `PERFECT=True`: 모든 통로를 연결하며, 순환이 없는 미로를 만듭니다.
- `PERFECT=False`: 기본 모드입니다. 연결된 미로에 벽을 더 열어 막다른길을
  줄이고, 최소 두 독립 순환을 만듭니다. 네 모서리와 중앙은 통로로 남습니다.

이 저장소는 Ubuntu 제출용입니다. 개발 레퍼런스의 실험, 학습 자료, 테스트,
Nix·direnv 설정은 포함하지 않습니다.

## Instructions

Ubuntu x86-64, Python 3.10 이상, `make`, [uv][uv-install]가 필요합니다.
시스템 도구는 사용자가 먼저 설치합니다. MLX에는 XCB, Vulkan, zlib, libbsd,
작동하는 그래픽 드라이버와 X11 화면이 필요합니다. Wayland에서는 XWayland가
필요합니다. `make install`은 시스템 라이브러리나 드라이버를 설치하지 않습니다.

저장소 루트에서 실행합니다.

```sh
make install
make run
```

과제에 명시된 명령을 직접 사용하려면 같은 가상환경을 활성화합니다.

```sh
source .venv/bin/activate
python3 a_maze_ing.py config.txt
```

`config.txt` 대신 다른 설정 파일 경로를 전달할 수 있습니다. 인자는 하나뿐입니다.

### 키와 화면

| 키 | 동작 |
| --- | --- |
| `R` | 다음 미로를 생성·저장한 뒤 화면 교체 |
| `P` | 최단 경로 표시·숨김 |
| `C` | 두 벽 색상 전환 |
| `Escape` / 창 닫기 | 종료 |

시작은 청록색, 끝은 산호색, 경로는 호박색, 닫힌 `42` 칸은 보라색입니다.
셀은 16픽셀, 벽은 2픽셀로 고정합니다. 화면에 맞춘 자동 축소는 하지 않으므로
큰 미로는 화면 밖으로 잘릴 수 있습니다. 미로 파일은 화면을 열기 전에 저장됩니다.

### 설치·검사·빌드

`make install`은 `uv sync --locked`로 `.venv`를 구성합니다. 생성기 소스는
editable 설치하고, `uv.lock`에 기록된 MLX·flake8·mypy를 함께 설치합니다.
MLX는 [동봉한 공식 Ubuntu wheel](third_party/mlx/README.md)에서 가져옵니다.
PyPI의 동명 `mlx`는 이 과제의 라이브러리가 아닙니다.

| 명령 | 동작 |
| --- | --- |
| `make debug` | `pdb`에서 기본 설정으로 실행 |
| `make lint` | `flake8 .` 및 과제 지정 플래그의 `mypy .` |
| `make lint-strict` | `flake8 .` 및 `mypy . --strict` |
| `make package` | 루트에 `mazegen-1.0.0-py3-none-any.whl` 빌드 |
| `make clean` | Python·mypy 캐시와 빌드 중간 파일 삭제 |

`make clean`은 `.venv`, 저장한 미로, 제출용 wheel을 지우지 않습니다.
의존성 변경 시 `uv lock`으로 잠금 파일을 갱신하고 함께 커밋합니다.
Python 자체와 격리 빌드 환경의 `setuptools>=77`은 이 잠금 파일로 고정되지 않습니다.
`make package`는 표준 빌드 백엔드인 setuptools를 격리 환경에서 사용합니다.

## Configuration

기본 설정은 다음과 같습니다.

```ini
WIDTH=25
HEIGHT=17
ENTRY=0,0
EXIT=24,16
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=42
```

| 키 | 필수 | 값 |
| --- | --- | --- |
| `WIDTH`, `HEIGHT` | 예 | 양의 정수인 가로·세로 칸 수 |
| `ENTRY`, `EXIT` | 예 | 서로 다르고 범위 안에 있는 `x,y` 좌표 |
| `OUTPUT_FILE` | 예 | 출력 파일 경로 |
| `PERFECT` | 예 | 정확히 `True` 또는 `False` |
| `SEED` | 아니요 | 정수. 0과 음수도 허용 |

한 줄에 `KEY=VALUE` 하나를 씁니다. 빈 줄과 `#`로 시작하는 주석 줄은 무시하고,
이름과 값 양쪽의 공백을 제거합니다. 키 이름은 대소문자를 구분합니다.
구분자가 빠지거나 키가 비어 있거나 지원하지 않는 이름이면 줄 번호와 함께
오류를 알립니다. 중복 키는 마지막 값을 사용합니다. 줄 끝 주석은 지원하지 않습니다.
입력 형식 오류는 설정 파일명과 원래 오류 메시지를 출력합니다.
상대 출력 경로는 설정 파일의 폴더가 아니라 실행한 작업 폴더를 기준으로 합니다.

`SEED`가 있으면 `Random(seed)`, 없으면 `Random()`에 해당하는 난수 객체를
한 번 만듭니다. 최초 생성과 모든 `R`이 이 객체를 공유합니다. 같은 설정·시드로
다시 실행하면 같은 생성 시도를 재현합니다. 시드를 증가시키거나 매번 난수
객체를 다시 만들지 않습니다. 빈 값이나 정수가 아닌 `SEED`는 오류입니다.
재현은 같은 구현과 Python 환경을 기준으로 하며, 연속 생성의 모양이 반드시
서로 다르다는 뜻은 아닙니다.

기본 모드는 `(WIDTH - 1) * (HEIGHT - 1) < 2`인 크기를 거부합니다. 그 크기는
벽을 모두 열어도 두 독립 순환을 만들 수 없습니다. 시작·끝이 배치된 `42`에
겹치는 경우도 오류입니다. 생성이나 저장이 실패하면 기존 화면은 유지하지만,
이미 소비한 난수는 되돌리지 않습니다. 저장 중 실패하면 파일이 일부만 기록될
수 있습니다.
예외 메시지가 비어 있으면 `MemoryError`처럼 예외 이름을 표시합니다.
초기 실행 오류는 종료 코드 1로 종료합니다. 실행 중 그리기 오류는 콜백에서
알리고 루프를 끝낸 뒤 이미지·창을 정리합니다. 이 경우 종료 코드는 0입니다.

## Algorithm and design

생성기는 외곽과 `42`를 제외한 이웃 중에서 반복형 무작위 DFS로 통로를 냅니다.
방문하지 않은 칸에만 진입하므로 연결된 트리가 생깁니다. 재귀 대신 스택을 써서
큰 미로에서도 Python의 재귀 깊이에 의존하지 않습니다.

기본 모드는 이 트리를 행 우선으로 훑으며 막다른길의 닫힌 벽을 북·동·남·서
순서로 하나 엽니다. 그래도 순환이 두 개 미만이면 남은 벽을 더 엽니다.
기존 통로를 닫지 않으므로 연결은 유지되고, 열린 벽 하나마다 독립 순환이
하나 증가합니다. 완성된 미로의 최단 경로는 BFS로 한 번 계산합니다.

DFS·막다른길 처리·BFS는 격자 칸 수에 선형인 시간과 메모리를 사용합니다.
Kruskal과 달리 전체 간선 목록과 분리 집합 자료구조를 추가로 만들지 않아도
되어, 생성 흐름을 직접 읽고 설명하기 쉽다는 이유로 이 방식을 선택했습니다.

열린 `3x3`이 생기지 않는 성질은 **DFS와 현재 막다른길 처리 순서의 조합**에
의존합니다. 다른 생성 알고리즘이나 순서로 바꾸면 다시 검증해야 합니다.
기본 모드는 제공 분석기의 `--max-dead-ends 0` 기준을 만족하지만, `42`나 외곽에
둘러싸인 피할 수 없는 주머니는 남습니다. 분석기는 이를 별도로 셉니다.
또한 전역 순환 두 개가 임의의 두 칸 사이에 독립 경로 두 개를 보장하지는 않습니다.

### 닫힌 `42` 문양

```text
#...###
#.....#
###.###
..#.#..
..#.###
```

원점은 `((WIDTH - 7) // 2, (HEIGHT - 5) // 2)`로 고정합니다. 짝수 크기의
중앙은 왼쪽·위쪽으로 결정하며, 문양의 가운데는 통로입니다.
문양과 연결을 함께 유지할 수 있는 최소 크기는 `8x6`입니다. 정확히 `8x6`이면
모서리 하나를 차지하므로 perfect 모드만 배치하고, 기본 모드는 `8x7` 또는
`9x6` 이상에서 배치합니다. 이 배치가 불가능하면 문양 없이 생성하되
`Error: maze is too small for 42`를 콘솔에 출력합니다.

## Output format

칸마다 네 벽의 상태를 16진수 한 자리로 저장합니다. 각 비트는 **1이면 벽이 있고,
0이면 통로**입니다. 북·동·남·서가 각각 `1`, `2`, `4`, `8`입니다.
예를 들어 `A`는 동쪽과 서쪽에 벽이 있다는 뜻입니다.

미로는 행마다 한 줄이며, 그 뒤 빈 줄, 시작 좌표, 끝 좌표, 최단 경로를 각각
한 줄에 씁니다. 경로는 `N`, `E`, `S`, `W`의 연속입니다. 마지막 줄도 `\n`으로
끝납니다. 두 칸짜리 perfect 미로의 예시는 다음과 같습니다.

```text
D7

0,0
1,0
E
```

## Reusing mazegen

루트의 wheel에는 생성기 코드·사용 설명·라이선스가 들어 있습니다. 앱, MLX,
PNG와 검사 도구는 들어가지 않습니다. 다른 가상환경에서도 일반 pip로 설치합니다.

```sh
python3 -m pip install mazegen-1.0.0-py3-none-any.whl
```

```python
from random import Random
from mazegen import EAST_BIT, MazeGenerator

rng = Random(42)
maze = MazeGenerator(25, 17, (0, 0), (24, 16), rng=rng, perfect=False)
print(maze.walls[0][0])
print(maze.entry, maze.exit)
print(maze.path)
print(bool(maze.walls[0][0] & EAST_BIT))
```

앞의 네 인자는 `width`, `height`, `entry_cell`, `exit_cell`입니다.
`rng`는 필수 키워드 인자이고, `perfect`의 기본값은 `False`입니다.
같은 `rng`를 다시 전달하면 난수 흐름이 이어집니다. `walls[y][x]`가 벽 코드이며,
`path`는 시작과 끝을 포함한 최단 경로의 `(x, y)` 좌표 튜플입니다.
[패키지 사용 설명](mazegen/README.md)에 모든 매개변수와 반환 구조, 예외와 제한을
정리했습니다.

## License

이 프로젝트의 자체 제작물은 [Blue Oak Model License 1.0.0](LICENSE.md)을
적용합니다. 후속 프로젝트에서 재사용하기 쉽고, 두 팀원이 권리와 의무를 직접
읽고 설명할 수 있으며, 특허 허락을 명시한다는 이유로 선택했습니다.
재배포할 때 라이선스 본문 또는 공식 링크를 전달합니다. 소스 공개나 변경 사실
표시를 요구하지 않지만, 모든 법적 위험이나 제삼자의 특허 문제를 해결하지는 않습니다.

동봉한 MiniLibX는 별도 저작물이며, 기존
[MIT 라이선스와 저작권 고지](third_party/mlx/LICENSE.md)를 그대로 유지합니다.
생성기 wheel에는 MiniLibX가 포함되지 않습니다.

## Team and project management

- `hyunlee`: `mazegen`의 생성·해결 로직과 공개 API를 담당합니다.
- `jungblee`: 설정·출력·MLX 앱, 빌드와 패키징을 담당합니다.
- 두 사람 모두 전체 코드를 설명하고, 상대 영역의 결과를 함께 검토합니다.

초기 계획은 작은 두 칸 미로로 벽·경로 형식을 맞춘 뒤, 생성기와 앱을 나누어
구현하고 통합·교차 검토·패키징으로 진행하는 것이었습니다. 레퍼런스를 발전시키며
여러 중간 객체와 실험적 화면 구성을 걷어내고, 생성기 패키지와 앱 한 파일이라는
책임 경계로 정리했습니다. 이 제출본은 그 결과에서 실행·빌드·설명에 필요한
파일만 추출한 것입니다. 추출 커밋은 팀원 각각의 구현 완료 기록을 뜻하지 않습니다.

잘 작동한 점은 벽과 경로라는 작은 전달 형식 덕분에 그래픽 없이 생성기를
검사하고, 알려진 미로로 앱을 검사할 수 있었다는 것입니다. 개선할 점은 구현을
고정하기 전에 과제 문장을 먼저 확인하는 것입니다. 실제로 시드의 세션 의미와
작은 미로의 `42` 배치 조건을 다시 검토했습니다. 최종 역할별 기여와 Ubuntu
실행·상호 리뷰 결과는 제출 전에 두 사람이 직접 확인해야 합니다.

도구는 Jujutsu/Git, uv, setuptools, flake8, mypy를 사용합니다. 별도 레퍼런스의
unittest와 과제 제공 분석기로 동작을 검사하며, 이 검사 코드는 제출하지 않습니다.
MLX를 대체한 자동 검사는 실제 화면·드라이버 검증을 대신하지 않습니다.

## Resources

- 과제 원문 A-Maze-ing v2.3 및 함께 제공된 `maze_analyzer.py`.
- [MiniLibX 2.2의 출처와 라이선스](third_party/mlx/README.md).
- [MIT: DFS][dfs], [MIT: BFS][bfs] — 그래프 탐색의 기본 원리.
- [Python random][random], [collections.deque][deque] — 난수 흐름과 BFS 큐.
- [uv 프로젝트 환경][uv-project], [Python 패키징 가이드][packaging].

AI는 요구사항 분류, 알고리즘·설계 대안 검토, 코드·테스트·문서의 초안과 수정,
제출 파일 추출 및 패키징 검증에 사용했습니다. 사람이 이해하거나 검증했다는
사실을 AI 작업으로 대신하지 않습니다. 두 팀원이 남긴 코드를 직접 설명하고,
실제 평가 환경에서 실행하며, 평가 중 간단한 변경도 할 수 있어야 합니다.

[uv-install]: https://docs.astral.sh/uv/getting-started/installation/
[uv-project]: https://docs.astral.sh/uv/guides/projects/
[packaging]: https://packaging.python.org/en/latest/tutorials/packaging-projects/
[random]: https://docs.python.org/3/library/random.html
[deque]: https://docs.python.org/3/library/collections.html#collections.deque
[dfs]: https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/lecture-14-depth-first-search-dfs-topological-sort/
[bfs]: https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/lecture-13-breadth-first-search-bfs/
