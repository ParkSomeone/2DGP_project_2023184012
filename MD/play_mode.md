# `play_mode.py` 작성 안내서

> 이 문서는 `play_mode.py`를 다른 프로젝트의 모드로 가져와 실행할 수 있도록 프레임워크 계약, 필요한 파일, 수정할 부분을 설명한다.

## 역할

`play_mode.py`는 실제 플레이 장면 하나를 구현하는 모듈이다. 프레임워크의 모드 계약에 맞춰 초기화, 입력, 업데이트, 렌더링, 종료 처리를 제공하며, 객체의 세부 동작은 각 객체 클래스에 맡긴다.

## 표준 모드 함수

```python
from pico2d import *
import game_framework
import game_world
from boy import Boy
from grass import Grass

boy = None

def init():
    global boy
    game_world.clear()
    boy = Boy()
    game_world.add_object(Grass(), 0)
    game_world.add_object(boy, 1)

def handle_events():
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        if event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
            return
        if boy is not None:
            boy.handle_event(event)

def update():
    game_world.update()

def render():
    clear_canvas()
    game_world.render()
    update_canvas()

def pause():
    pass

def resume():
    pass

def finish():
    global boy
    game_world.clear()
    boy = None
```

모드가 활성화되면 프레임워크가 `init()`을 한 번 호출하고, 루프에서 `handle_events()` → `update()` → `render()`를 반복한다. 전환 방식에 따라 `pause()`/`resume()`을 호출하고, 완전히 벗어날 때 `finish()`를 호출한다.

위 코드는 연결 구조 예시다. 대상 객체가 `handle_event()`를 제공하지 않는다면 모드에서 해당 호출을 제거하거나 객체에 메서드를 구현한다.

## 초기화와 객체 등록

`init()`에서 월드를 비우고 이 모드가 사용할 객체를 생성한다. 배경과 캐릭터를 서로 다른 레이어에 놓아 렌더링 순서를 명시한다.

```python
def init():
    game_world.clear()
    game_world.add_object(Grass(), 0)
    game_world.add_object(Boy(), 1)
```

현재 LEC15·LEC16 실습본은 월드 추가 함수 이름이 `add_oject()`로 오타가 나 있다. 재사용용 코드에서는 `game_world.md`의 권장 이름 `add_object()`를 사용하고, 월드 정의와 호출부를 함께 맞춘다.

## 입력 처리

`handle_events()`는 이벤트를 한 곳에서 읽는다. 창 닫기나 전역 종료 키는 `game_framework.quit()`으로 처리하고, 게임 플레이 입력은 캐릭터 등 해당 객체의 `handle_event(event)`로 전달한다. 모드 전환을 요청한 뒤에는 같은 이벤트를 다른 객체에 중복 전달하지 않도록 즉시 반환한다.

일시정지 화면을 띄우는 경우 `game_framework.push_mode(pause_mode)`를 사용하면 현재 플레이 모드가 스택에 남는다. 일시정지 모드에서 `pop_mode()`를 호출하면 플레이 모드의 `resume()`이 실행된다. 플레이 모드로 완전히 이동하는 경우에는 `change_mode()`를 사용한다.

## 시간 기반 업데이트

LEC16 패턴에서는 객체가 `game_framework.frame_time`을 이용해 실제 경과 시간만큼 이동·애니메이션한다. `play_mode.update()`는 월드의 업데이트를 호출하고, 시간 단위 계산은 각 객체에 둔다. `delay()`는 테스트를 위해 프레임을 늦출 때 쓸 수 있지만, 정상적인 이동 속도 계산을 대신하지 않는다.

## 다른 프로젝트에 복사하기

플레이 모드는 단독 실행 파일이 아니다. 다음 파일과 계약을 함께 맞춘다.

| 필요한 것 | 요구사항 |
|---|---|
| `game_framework.py` | 위에서 설명한 모드 콜백을 호출하고 `run()` 제공 |
| `game_world.py` | `clear`, `add_object`, `update`, `render` 제공 |
| 객체 모듈 | 여기서는 `boy.py`, `grass.py`; 생성자 및 메서드가 모드 코드와 일치 |
| 그래픽·입력 라이브러리 | 예제의 `pico2d` 및 그 환경의 SDL 이벤트 상수 |
| 리소스 | 객체에서 로드하는 이미지·폰트 파일 |

LEC16 실습 파일을 그대로 쓸 경우 추가로 `ball.py`, `animation_sheet.png`, `ball21x21.png`, `ball41x41.png`, `ruler.png`, `ENCR10B.TTF`가 필요하고 `transitions` 패키지가 사용된다. `main.md`의 파일 구성 예와 실제 import 및 `load_image()`/`load_font()` 호출을 대조해 누락을 찾는다.

1. 모드·월드·프레임워크 파일을 복사하고 Python import 경로가 맞는지 확인한다.
2. 예제의 `Boy`, `Grass`와 이미지 이름을 새 프로젝트의 객체 및 리소스로 바꾼다.
3. `game_world.add_object(obj, layer)` API와 레이어 번호를 월드 구현에 맞춘다.
4. 프레임워크가 요구하는 일곱 모드 함수가 정의되어 있는지 확인한다. 사용하지 않는 `pause()`/`resume()`도 `pass`로 둔다.
5. 캔버스 크기, 입력 상수, 리소스 경로를 점검하고 `main.py`에서 이 모듈을 시작 모드로 전달한다.

현재 예제의 `finish()`는 전역 월드를 모두 비운다. 여러 모드가 같은 월드에 동시에 객체를 두는 설계라면, 모드 종료 때 전역 `clear()`를 호출하지 말고 그 모드 소유 객체만 제거하도록 월드 API와 소유권을 설계한다.

## 이 저장소의 추격 스테이지 구현

현재 `sorce/play_mode.py`는 시작 모드로 실행되는 추격 스테이지 프로토타입이다. 플레이어는 `sorce/player.py`, 몬스터는 `sorce/monster.py`, 보스는 `sorce/boss.py`, 공통 스테이지 오브젝트와 스폰은 `sorce/stage_objects.py`에서 관리하며, 수치는 `sorce/stage_config.py`에 둔다. 캔버스는 16:9의 1600×900이다.

- A/D로 좌우 이동하고, 스페이스바로 점프한다. 발판 위에서 S를 누른 채 스페이스바를 누르면 아래 발판으로 떨어진다. 발판은 기존 길이의 2/3로 짧아졌다. 발판은 화면 왼쪽 밖에서 생성되어 오른쪽으로 이동하며, 초기 발판과 새 발판마다 1~3마리의 몬스터가 무작위로 함께 생성된다. 바닥 몬스터는 2초마다 50% 확률로 화면 왼쪽 밖에 소환된다. 캐릭터는 화면 오른쪽에서 시작하며 왼쪽을 향해 달리는 애니메이션을 반복한다. 배경과 바닥은 왼쪽으로 흐른다.
- W/E/R을 눌러 사용 가능한 액티브 스킬을 조준 상태로 선택하고, 마우스 왼쪽 클릭으로 발사한다. 3초 동안 조준하면 스킬이 자동 발동한다. 오른쪽 클릭 또는 조준 중 Escape로 취소한다. 조준점이 캐릭터보다 오른쪽이면 캐릭터도 오른쪽을 바라보고, 그 외에는 왼쪽을 향한다.
- Q로 물약을 사용하고, 몬스터 처치 시 자동 공격을 시도한다. 보물상자는 먼저 현재 출현 가능한 층(바닥 또는 화면에 들어온 발판 층)을 무작위로 선택한 뒤, 선택한 층에 나타난다. 보스는 고정 위치에 있으며 액티브 스킬만 피해를 준다.
- 조준 중 스테이지 2분 카운터와 배경·발판·캐릭터·투사체 등 이동량은 0.5배다. 액티브 쿨타임, 피격 경직 및 무적 타이머는 실제 경과 시간으로 진행한다.
- 프로토타입 밸런스 수치와 임시 스킬 동작은 `sorce/stage_config.py`에서 조정한다. 이미지 파일은 표준 라이브러리만 사용하는 `sorce/generate_stage_assets.py`로 `image/`에 생성한다.
- 강화, 스테이지 선택, 게임오버, 클리어 화면은 범위 밖이다. 모드 전환을 연결할 코드가 아직 없으므로 `play_mode.consume_events()`가 `chest_collected`, `upgrade_requested`, `survived`, `player_died`, `boss_defeated` 등의 이벤트를 반환한다.
- 패시브 스킬은 효과와 발동 규칙이 정해지지 않아 아직 실제 효과를 구현하지 않았다.

프로젝트 루트에서 `python sorce\main.py`로 실행한다. W/E/R 효과, 자동 공격 주기, 적 체력, 발판 생성 간격 등은 기획 확정값이 아니라 플레이 가능한 임시값이다.

## 작성 규칙과 주의점

- 모드 함수의 이름은 프레임워크가 호출하는 계약과 일치시킨다. `draw()`를 쓴 프레임워크라면 모드도 `draw()`를 제공해야 하며, 현재 실습본은 `render()`를 호출한다.
- 이벤트, 월드 업데이트, 화면 렌더링 코드를 각 함수에 분리한다.
- 전역으로 유지해야 하는 객체 참조는 모듈 수준 변수로 두고, 함수 안에서 재할당할 때 `global`을 선언한다. 꼭 필요한 상태만 보관한다.
- `finish()`에서 월드 객체·리소스를 정리하고 모드 전환 후 이전 장면이 남지 않게 한다.
- 모드를 여러 번 다시 시작해도 객체나 리소스가 중복 생성되지 않도록 `init()`/`finish()`를 짝으로 설계한다.

## 참고 자료 (선택)

PDF는 추가 학습용 출처이며, 모드 계약 및 이식 절차는 위 설명만으로 확인할 수 있다.

- `LEC15_게임프레임웍.pdf`, `LEC14_게임월드.pdf`, `LEC16_시간.pdf`
- 실습 예제: `Labs/LEC15_Game_Framework/play_mode.py`, `Labs/LEC16_Time/play_mode.py`
