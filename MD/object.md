# 게임 객체 모듈 작성 안내서 (`object.py`)

## 역할

게임 객체(Game Object)는 게임 월드를 이루는 요소다. LEC11 강의는 객체를 속성(현재 상태를 나타내는 데이터)과 행동(시간이나 이벤트에 따라 상태를 바꾸는 기능)의 묶음으로 소개한다. 예를 들어 캐릭터는 위치·방향·애니메이션 프레임을 갖고, 업데이트와 입력에 따라 이를 바꾼 뒤 화면에 그린다.

이 안내서는 특정 게임의 `object.py` 파일을 그대로 제공하는 API 설명이 아니라, 새 프로젝트에서 게임 객체를 담는 `object.py`를 작성하고 게임 프레임워크·월드에 연결하기 위한 재사용 규칙이다. 실습처럼 객체 수가 늘어나면 `boy.py`, `ball.py`, `grass.py`로 나누어도 된다.

## 기본 클래스 구조

```python
from pico2d import load_image

class GameObject:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = load_image('object.png')

    def update(self):
        pass

    def draw(self):
        self.image.draw(self.x, self.y)
```

위 코드는 객체 인터페이스 예시다. 실제 프로젝트의 `object.py`에 붙여넣을 때 `object`라는 파일명은 Python 내장 타입과 이름이 비슷하므로 `game_object.py`처럼 구체적인 모듈명을 권장한다. 기존 요구로 `object.py`를 유지해야 한다면 다른 코드나 패키지 이름과 충돌하지 않는지 확인한다.

- 클래스 이름은 대문자로 시작하는 `PascalCase`, 모듈명은 소문자 `snake_case`로 짓는다. (`Boy`, `boy.py`)
- `__init__(self, ...)`에서 인스턴스별 초기 상태를 설정한다. `self`는 현재 인스턴스를 가리키는 첫 번째 매개변수다.
- `update()`는 게임 상태를 갱신하고, `draw()`는 그 상태를 화면에 표현한다. 월드가 두 메서드를 호출하므로 등록 대상은 두 메서드를 모두 제공한다.
- 이벤트가 필요한 객체만 `handle_event(event)`를 구현하고, 모드가 이벤트를 객체에 전달한다. 모드가 `handle_event()`를 호출하는데 객체에 해당 메서드가 없으면 런타임 오류가 나므로 호출부와 객체 인터페이스를 함께 맞춘다.
- 객체는 자신을 월드 리스트에서 직접 순회하거나 화면 전체를 지우지 않는다. 필요한 경우 `game_world` API로 자신을 추가·제거한다.

## 속성과 리소스

위치·방향·속도·프레임처럼 인스턴스마다 다른 값은 `self`에 저장한다. 모든 인스턴스가 공유할 수 있는 이미지 캐시는 클래스 변수로 둘 수 있다. LEC12~16 실습의 공 패턴은 이미지 종류별로 한 번만 로드하고 각 공 인스턴스가 참조하게 한다.

리소스 로드 위치는 실행 작업 디렉터리에 영향을 받으므로 이미지·폰트 파일을 코드가 찾는 경로에 함께 둔다. 모드 전환 후 리소스가 불필요하게 남지 않도록 수명과 소유자를 정한다.

## 예제에서 발전한 패턴

- `Grass`: 정적인 배경도 `update()`와 `draw()`를 제공한다. 변화가 없으면 `update()`는 `pass`일 수 있다.
- `Boy`: 위치, 방향, 입력 상태, 애니메이션 상태를 보유한다. 이벤트 처리와 시간 기반 이동은 이 객체가 맡는다.
- `Ball`: 위치와 속도를 보유해 업데이트마다 이동하고, 화면 밖으로 나가면 `game_world.remove_object(self)`를 호출한다.

## 시간 기반 동작

프레임 속도에 좌우되지 않게 이동량은 속도(픽셀/초)에 `game_framework.frame_time`(초)을 곱한다.

```python
self.x += self.direction * self.speed * game_framework.frame_time
```

애니메이션 프레임도 초당 프레임 수에 `frame_time`을 곱해 증가시킨다. 정수 프레임 인덱스가 필요할 때는 그릴 때 정수로 변환한다.

## LEC12 목표 상태 다이어그램: IDLE 하나만 구현하기

LEC12 첫 단계의 목표는 캐릭터가 제자리에 서서 IDLE 애니메이션만 반복하는 것이다. 이 단계에는 키 입력이나 다른 상태로의 전이가 없다.

```text
             ┌───────────────┐
      시작 ─▶│ IDLE          │
             │ 위치 유지     │
             │ 프레임 0..7 반복│
             └───────↺───────┘
```

`transitions`의 `Machine`을 캐릭터 인스턴스에 연결하고, 시작 상태를 `IDLE`로 지정한다. 아직 전이 규칙을 정의하지 않으므로 캐릭터는 계속 IDLE 상태에 머문다.

```python
from pico2d import load_image
from transitions import Machine

class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.image = load_image('animation_sheet.png')
        self.machine = Machine(
            model=self,
            states=['IDLE'],
            initial='IDLE',
            auto_transitions=False,
        )

    def update(self):
        if self.state == 'IDLE':
            self.frame = (self.frame + 1) % 8

    def draw(self):
        if self.state == 'IDLE':
            self.image.clip_draw(
                self.frame * 100, 300, 100, 100, self.x, self.y
            )
```

이 예제는 `animation_sheet.png`에서 IDLE 애니메이션이 100×100 프레임 8개로 구성되고, IDLE 행의 y 오프셋이 300인 실습 리소스를 전제로 한다. 다른 스프라이트 시트를 사용할 때 프레임 크기, 행 위치, 프레임 수, 캐릭터 좌표를 그 리소스에 맞춘다. `self.state`는 `Machine`이 모델에 제공하는 현재 상태 이름이다.

### `transitions` 모듈 설치

`transitions`는 Python 기본 내장 모듈이 아니므로, 게임 실행에 사용하는 Python 환경에 설치해야 한다. Windows PowerShell 또는 터미널에서 다음을 실행한다.

```powershell
python -m pip install transitions
python -m pip show transitions
python -c "from transitions import Machine; print('transitions import OK')"
```

여러 Python 설치본이나 가상환경이 있다면 `python`이 게임을 실행하는 인터프리터인지 먼저 확인한다. VS Code에서는 선택된 인터프리터의 터미널에서 설치하고, 게임 실행도 같은 인터프리터로 한다. `No module named 'transitions'`가 계속되면 다른 환경에 설치했을 가능성이 높다. `pico2d` 및 SDL 관련 의존성은 `transitions` 설치만으로 함께 설치되지 않으며 별도로 준비해야 한다.

## 다른 모듈과 연결

1. 모드의 `init()`이 객체를 생성하고 `game_world.add_object(obj, layer)`로 등록한다.
2. 프레임워크가 모드 업데이트를 호출하고, 모드는 `game_world.update()`를 호출한다.
3. 월드는 각 객체의 `update()`를 부른다.
4. 모드가 `game_world.render()`를 호출하면 월드가 객체의 `draw()`를 부른다.
5. 입력이 필요한 객체는 모드로부터 이벤트를 전달받는다.

## 다른 프로젝트에서 사용하기

1. `object.py` 또는 권장 이름인 `game_object.py`를 게임 모듈들이 import할 수 있는 폴더에 둔다.
2. `pico2d`를 사용하지 않는 프로젝트라면 `load_image()`와 `image.draw()`를 대상 엔진의 리소스 로더·렌더 호출로 바꾼다. 엔진과 독립된 로직을 원하면 객체는 위치와 상태만 관리하고, 별도의 렌더러가 `draw()`를 구현하도록 계약을 나눈다.
3. 생성자 매개변수와 리소스 경로를 프로젝트에 맞게 바꾼다. 리소스 로드는 객체마다 반복하지 않도록 클래스 캐시나 프로젝트의 자산 관리자를 사용한다.
4. 월드 등록 전에 객체가 월드가 요구하는 `update()`와 `draw()` 메서드를 구현하는지 확인한다. 이벤트 전달도 `handle_event(event)` 지원과 호출부를 함께 확인한다.
5. 위치·속도의 단위를 프로젝트 전체에서 통일한다. 시간 기반 이동을 쓸 경우 초당 속도와 프레임 경과 시간(초)을 곱한다.
6. 화면 밖 제거나 충돌 처리에서 `game_world.remove_object(self)`를 호출한다면 해당 월드 API가 존재하고 제거 중 순회가 안전한지 확인한다.

### 의존성

위 예제는 `pico2d`의 이미지 로딩·그리기 API를 사용한다. `game_framework.frame_time`을 참조하는 구체 객체(예: 실습의 `Boy`)는 프레임워크에도 의존한다. 상태 머신을 그대로 옮기는 객체는 `transitions` 패키지를 추가로 import할 수 있으므로 해당 코드의 import를 확인해 의존성을 준비한다. `object.py`라는 파일명 자체에는 특별한 게임 기능이 없으며, 예제 클래스와 호출 계약에 따라 필요한 라이브러리가 달라진다.

## 참고 자료 (선택)

- 아래 PDF는 작성 배경을 더 알고 싶을 때 참고할 수 있으며, 이 문서를 사용하기 위한 필수 자료는 아니다: `LEC11_게임오브젝트.pdf`, `LEC12_캐릭터컨트롤러(1).pdf`, `LEC13_캐릭터컨트롤러(2).pdf`, `LEC14_게임월드.pdf`, `LEC16_시간.pdf`.
- 실습 예제: `Labs/LEC11_GameObject/boy_grass_object.py`, `Labs/LEC14_Game_World/`, `Labs/LEC15_Game_Framework/`, `Labs/LEC16_Time/`
