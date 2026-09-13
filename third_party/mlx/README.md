# MiniLibX 2.2

과제와 함께 제공된 `mlx-2.2.tgz`의 Ubuntu x86-64 wheel을 수정 없이 사용합니다.
파일명은 `py3-none-any`이지만 내부의 `libmlx.so`는 Linux x86-64 바이너리입니다.

- 파일: `ubuntu/mlx-2.2-py3-none-any.whl`
- SHA-256: `7a1a44b50b6295f574522ba1a1e589632c6299d193dec57c951e8fdfb3337195`
- 원본 아카이브 SHA-256: `17c7197e0a0bdc6aa2172c14c712f2d16832f19485ca6f7aa94ddeff46346783`
- 저작권: 2025 42 Born2code - Olivier CROUZET
- 라이선스: 이 폴더의 [LICENSE.md](LICENSE.md), MIT

프로젝트 설치는 `pyproject.toml`의 로컬 경로를 사용합니다. 이 의존성은
앱 실행 환경에만 설치되며, 독립 `mazegen` 패키지의 의존성에는 들어가지 않습니다.
호스트에는 XCB, Vulkan, zlib, libbsd와 작동하는 그래픽 드라이버가 필요합니다.
X11 화면이 필요하며, Wayland 환경에서는 XWayland가 필요합니다.

## API 확인

Python 래퍼와 C API 문서는 위 wheel에 함께 들어 있습니다. `make install` 후
저장소 루트에서 다음 명령으로 설치된 래퍼 위치를 확인합니다.

```sh
.venv/bin/python -c 'import inspect; from mlx import Mlx; print(inspect.getfile(Mlx))'
```

출력된 `mlx.py`와 같은 폴더를 기준으로 읽습니다. Python 버전에 따라
`.venv/lib/python3.x/site-packages/mlx/`의 경로가 달라집니다.

| 파일 | 확인할 내용 |
| --- | --- |
| `mlx.py` | 실제 Python 메서드의 인자·반환값, 콜백 연결 |
| `docs/mlx.h` | C API 전체 목록과 상수, 자원과 이미지 형식의 계약 |
| `docs/mlx.3`, `docs/mlx_new_window.3` | 초기화·해제, 창 생성·파괴 |
| `docs/mlx_new_image.3` | PNG 읽기, 이미지 메모리·stride·픽셀 형식, 화면 표시 |
| `docs/mlx_loop.3` | 이벤트 루프, 키·노출·일반 콜백, 루프 종료 |
| `docs/mlx_extra.3` | `mlx_sync`와 동기화 명령 |
| `test/simple_test.py` | 창 생성 → 콜백 등록 → 이벤트 루프의 제공 예제 |

`.3`은 C API의 man 문서입니다. 편집기로 읽거나 그 파일이 있는 `docs` 폴더에서
`man -l mlx_new_image.3`처럼 열 수 있습니다. Python 호출 형태는 `mlx.py`를
함께 확인해야 합니다. C에서 출력 포인터로 받는 값은 Python에서 튜플로 반환합니다.
예를 들어 `mlx_get_data_addr(image)`는 `(memoryview, bits_per_pixel, stride,
pixel_format)`을 반환하며, 마지막 값은 endian이 아니라 픽셀 형식입니다.

앱의 `self.api`는 이 래퍼의 `Mlx` 객체이고, `self.mlx`는 `mlx_init()`이 반환한
네이티브 컨텍스트 핸들입니다. `Window`, `draw()`, `draw_tile()`은 MLX API가
아니라 이 프로젝트에서 작성한 코드입니다.
