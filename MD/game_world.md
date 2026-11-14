# `game_world.py` 작성 안내서

> 이 문서는 월드 관리 파일을 다른 프로젝트에 복사해 객체와 연결할 수 있도록 필요한 자료 구조와 API 계약을 설명한다.

## 역할

`game_world.py`는 게임에 존재하는 객체를 모아 관리한다. 모드나 `main.py`가 객체마다 직접 `update()`와 `draw()`를 호출하는 대신, 월드에 등록된 객체를 순회하도록 한다. LEC14 슬라이드는 이를 단일 객체 목록에서 시작해, 그리기 순서를 위한 레이어(depth)가 있는 목록으로 발전시킨다.

## 데이터 구조와 레이어

레이어별 리스트를 담은 리스트를 사용한다. 낮은 인덱스의 레이어를 먼저 업데이트·렌더링하므로, 배경을 앞쪽 레이어(예: 0), 캐릭터·효과를 뒤쪽 레이어(예: 1)에 두는 식으로 그리기 순서를 정한다.

```python
world = [[], [], []]  # 0: 배경, 1: 게임 객체, 2: UI

def add_object(obj, layer=1):
    world[layer].append(obj)

def remove_object(obj):
    for objects in world:
        if obj in objects:
            objects.remove(obj)
            return

def update():
    for objects in world:
        for obj in objects[:]:
            obj.update()

def render():
    for objects in world:
        for obj in objects[:]:
            obj.draw()

def clear():
    for objects in world:
        objects.clear()
```

예제의 공개 함수와 인자는 `add_object(obj, layer=1)`, `remove_object(obj)`, `update()`, `render()`, `clear()`다. 레이어 수와 기본 레이어는 게임에 맞게 조정할 수 있지만, 객체를 등록하는 모든 호출부에서 같은 규칙을 사용해야 한다.

`objects[:]`는 순회 중인 리스트의 복사본이다. 객체가 `update()`나 `draw()` 중 월드에서 추가·삭제되어도 현재 순회가 바뀌지 않게 한다. 월드 구현마다 이 방어가 있는지 확인한다.

## API 작성 원칙

- `add_object(obj, layer=...)`: 객체 한 개를 지정한 레이어에 추가한다. 기본 레이어를 정하고 호출부와 일관되게 사용한다.
- `remove_object(obj)`: 첫 번째로 발견한 객체를 제거한다. 현재 예제는 객체가 없으면 아무 일도 하지 않으며, 같은 객체가 중복 등록된 경우 첫 번째 항목만 제거한다. 다른 정책이 필요하면 이 함수와 호출부의 기대 동작을 함께 바꾼다.
- `update()`: 등록된 객체의 `update()`를 호출한다.
- `render()`: 등록된 객체의 `draw()`를 호출한다.
- `clear()`: 모든 레이어를 비워 모드 재진입 시 이전 객체가 남지 않게 한다.

## 객체 계약

월드에 넣는 객체는 최소한 `update()`와 `draw()` 메서드를 제공한다. 변화가 없는 객체도 순회 규칙을 단순하게 유지하려면 `update()`에서 `pass`를 사용할 수 있다. 추가 API를 도입한다면 그 API를 호출하는 모든 객체가 구현하도록 계약을 함께 갱신한다.

## 다른 모듈과 연결

- 모드의 `init()`에서 `clear()` 후 필요한 배경·캐릭터 등을 추가한다.
- 모드의 `update()`는 `game_world.update()`를 호출한다.
- 모드의 `render()`는 화면을 지우고 `game_world.render()`를 호출한 뒤 화면 갱신 함수를 부른다.
- 객체가 생성·제거될 때는 `game_world.add_object()` 및 `remove_object()`를 사용한다.

## 다른 프로젝트에 복사하기

1. 위 예제를 `game_world.py`로 저장하고, 모드 및 객체 모듈에서 import 가능한 폴더에 둔다. 이 모듈 자체는 그래픽 라이브러리를 사용하지 않는다.
2. 프로젝트 전반의 함수명을 `add_object()`로 통일한다. 다른 API명을 이미 사용하는 경우 월드 함수와 모든 호출부를 함께 바꾼다.
3. 각 객체가 `update()`와 `draw()`를 제공하는지 확인한다. 월드는 두 메서드를 인자 없이 호출한다.
4. 등록 시 전달하는 레이어 번호가 `world`의 유효한 인덱스인지 확인한다. 범위를 벗어나면 `IndexError`가 발생한다.
5. 모드 시작 시 `clear()`를 호출하고 객체를 등록한다. 장면 교체 시에도 이전 객체가 남지 않도록 정리 정책을 적용한다.

현재 LEC15·LEC16 실습본은 `world = [[], [], []]`, 기본 레이어 `1`로 시작한다. LEC14 예제는 두 레이어를 두고 기본값을 `0`으로 둔다. 복사 후 사용할 레이어 수·기본값·깊이 의미를 프로젝트 전체에서 하나로 결정한다.

## 실습본 간 호환 문제

LEC14 실습본은 `add_object()`를 사용하지만, LEC15·LEC16의 `game_world.py`에는 `add_oject()`라는 철자 오류가 있고 해당 실습 모드도 그 이름을 호출한다. 재사용용으로는 `add_object()`로 고치고 호출부도 함께 변경한다. 또한 LEC14 버전은 객체 리스트를 직접 순회하므로 순회 중 리스트를 변경하면 요소를 건너뛸 수 있다. 동적 추가·삭제가 있는 프로젝트에서는 위 예제처럼 복사본을 순회하거나 변경을 별도 큐에 모은다.

## 참고 자료 (선택)

PDF는 추가 학습용 출처이며, API와 이식 절차는 위 설명만으로 확인할 수 있다.

- `LEC14_게임월드.pdf`, `LEC11_게임오브젝트.pdf`
- 실습 예제: `Labs/LEC14_Game_World/game_world.py`, `Labs/LEC15_Game_Framework/game_world.py`, `Labs/LEC16_Time/game_world.py`
