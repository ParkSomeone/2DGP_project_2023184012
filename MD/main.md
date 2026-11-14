# `main.py` 작성 안내서

> 이 문서는 강의 PDF 없이 다른 프로젝트에 파일을 복사해 연결할 수 있도록 작성한 사용 안내서다. 아래의 파일 구성, 의존성, 호출 규약을 기준으로 이식한다.

## 역할

`main.py`는 게임을 시작하고 종료하는 진입점이다. 게임 모드나 객체의 상세 동작을 직접 구현하지 않고, 캔버스를 준비한 뒤 `game_framework`에 첫 모드를 전달한다. 이처럼 실행 진입점을 분리하면 다른 모드나 게임 객체를 바꾸어도 실행 절차를 한곳에서 유지할 수 있다.

## 기본 구성

```python
from pico2d import open_canvas, close_canvas
import game_framework
import play_mode as start_mode

def main():
    open_canvas(1600, 600)
    try:
        game_framework.run(start_mode)
    finally:
        close_canvas()

if __name__ == '__main__':
    main()
```

`if __name__ == '__main__':`은 다른 모듈에서 `main.py`를 import할 때 게임이 자동 실행되는 것을 막는다. `try/finally`는 게임 루프가 예외로 끝나도 캔버스 닫기를 시도한다.

1. `start_mode`에 실행할 모듈을 지정한다. 로고부터 시작하려면 `logo_mode`, 곧바로 플레이하려면 `play_mode`를 가져온다.
2. 캔버스 크기를 게임의 좌표계와 일치시켜 연다.
3. 모듈 객체를 `game_framework.run(start_mode)`에 전달한다.
4. 프레임워크가 끝난 뒤 캔버스를 닫는다.

## 다른 프로젝트에 복사하기

다음은 LEC16 실습의 `play_mode.py`, `boy.py`, `grass.py`, `ball.py`를 그대로 사용할 때의 파일 구성 예다.

```text
my_game/
    main.py
    game_framework.py
    game_world.py
    play_mode.py
    boy.py
    ball.py
    grass.py
    animation_sheet.png
    ball21x21.png
    ball41x41.png
    grass.png
    ruler.png
    ENCR10B.TTF
```

- `main.py`, `game_framework.py`, `game_world.py`, `play_mode.py`를 같은 폴더에 두어 모듈 import가 되도록 한다.
- 이 구성은 `pico2d`, SDL 바인딩(`sdl2`), `transitions`를 사용할 수 있는 Python 환경을 전제로 한다. `transitions`는 상태 머신을 쓰는 `boy.py`가 import한다. 설치·SDL 설정은 대상 운영체제 및 프로젝트 환경에 맞춘다.
- 각 `.py` 파일의 import를 따라 필요한 모듈을 모두 복사한다. 예를 들어 `play_mode.py`는 `boy.py`와 `grass.py`를 가져오고, `boy.py`는 `ball.py` 및 `game_framework.py`를 사용한다.
- 이미지·폰트는 각 객체가 로드하는 파일을 빠짐없이 함께 둔다. 예제는 상대 경로 파일명을 사용하므로 프로젝트 루트에서 실행하고 리소스를 그 위치에 두는 것이 가장 단순하다.
- 모드가 `game_world.add_object()`를 부르도록 맞추고, 월드 모듈에도 같은 함수명이 있는지 확인한다. LEC15·LEC16 실습본의 `add_oject()` 철자 오류를 그대로 복사하지 않는다.
- 복사 후 게임과 같은 Python 실행 환경에서 `import pico2d`, `import sdl2`, `import transitions`가 되는지 확인하고 `python main.py`로 실행한다. 캔버스 표시, 입력, 종료 및 이미지·폰트 로드를 확인한다.

## 작성 규칙

- 파일은 프로젝트의 실행 진입점으로 하나 둔다. 보통 파일명은 소문자 `main.py`로 한다.
- 모드 전환, 입력 처리, 월드 업데이트 코드를 `main.py`에 몰아넣지 않는다. 각 책임은 각각 `game_framework.py`, 모드 모듈, `game_world.py`와 게임 객체에 둔다.
- 모듈을 import하는 이름은 파일명과 일치해야 한다. 예를 들어 `play_mode.py`는 `import play_mode`로 가져온다.
- 이미지·폰트 경로가 상대 경로라면 프로그램을 실행하는 작업 디렉터리와 리소스 파일의 위치를 일치시킨다.
- 캔버스 크기와 게임 객체 좌표, 배경 이미지 크기를 함께 조정한다. 창 크기만 바꾸면 객체 위치와 화면 구성이 자동으로 바뀌지는 않는다.

## 실행 흐름

`main.py` → `game_framework.run(start_mode)` → 시작 모드의 `init()` → 반복되는 이벤트·업데이트·렌더링 → 프레임워크의 `finish()` 정리 → `main.py`의 캔버스 종료 순서다.

## 참고 자료 (선택)

내용 이해를 위한 출처이며, 이 문서와 파일을 사용하는 데 PDF가 필요하지 않다.

- `LEC15_게임프레임웍.pdf`, `LEC16_시간.pdf`
- 실습 예제: `Labs/LEC15_Game_Framework/main.py`, `Labs/LEC16_Time/main.py`
