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
