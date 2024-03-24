from random import randint
import sys
import pygame_gui
import pygame
import pytmx

pygame.mixer.pre_init(44100, -16, 1, 512) # важно вызвать до pygame.init()
pygame.init()

money = pygame.mixer.Sound("music1/dengi-na-igrovoy-schet.ogg")
step_hero = pygame.mixer.Sound("music1/odinochnyiy-schelchok.ogg")
victory = pygame.mixer.Sound("music1/zvuk-pobedyi.ogg")
step_enemy = pygame.mixer.Sound("music1/zvuk-shaga.ogg")
game_ov = pygame.mixer.Sound("music1/konets-igri.ogg")
# Кортеж размеров окна
WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 672, 608

FPS = 15  # Частота. Количество кадров в секунду.

MAPS_DIR = "maps"  # Указание на папку где хранятся карты
TILE_SIZE = 32  # Размер квадратной ячейки (тайла)
ENEMY_EVENT_TYPE = 30  # Тип события для таймера противника.

# -------------------------------------------------Заставка
screen = pygame.display.set_mode(WINDOW_SIZE)
clock = pygame.time.Clock()


def terminate():
    pygame.quit()
    sys.exit()


def start_screen():
    manager = pygame_gui.UIManager((672, 608))  # Менеджер обрабатывает элементы пользовательского интерфейса
    # Ставим кнопку в середину экрана, она будет менять цвет экрана с белого на черный.
    switch = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((100, 300), (100, 50)),
        text='Старт', manager=manager
    )
    color = 'white'  # Переменная отвечает за цвет

    intro_text = ["Игра 'Догони'",
                  "Правила игры:",
                  "Если в правилах несколько строк,",
                  "приходится выводить их построчно"]
    fon = pygame.image.load('images/fon.jpg')

    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('brown'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        time_delta = clock.tick(60) / 1000.0  # Создадим переменную для работы с временем
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == switch:
                    return
            # elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            # return  # начинаем игру
            manager.process_events(event)  # настраиваем менеджер
        manager.update(time_delta)  # настраиваем менеджер
        manager.draw_ui(screen)  # настраиваем менеджер
        pygame.display.flip()
        clock.tick(FPS)


# -----------------------------------------------------------

class Labyrinth:
    # Конструктору передается имя файла с картой,
    # список тайлов по которым игрок может перемещаться,
    # модификатор тайла до которого нужно дойти.

    def __init__(self, filename, free_tile, finish_tile):

        self.map = pytmx.load_pygame(f"{MAPS_DIR}/{filename}")  # Берем карту из файла

        self.height = self.map.height  # Высота лабиринта
        self.width = self.map.width  # Ширина лабиринта
        self.tile_size = self.map.tilewidth
        self.free_tile = free_tile
        self.finish_tile = finish_tile
        self.score = 0

    # Функция для рисования лабиринта

    def render(self, screen):

        # Отразим на экране
        for y in range(self.height):
            for x in range(self.width):
                image = self.map.get_tile_image(x, y, 0)  # Метод передает координаты и номер слоя
                screen.blit(image, (x * self.tile_size, y * self.tile_size))
        font = pygame.font.Font(None, 32)  # Шрифт по умолчанию. Размер 24.
        text = font.render(f"Всего набрано: {self.score}", 1, (255, 0, 0))  # Текст, параметр сглаживания и цвет.
        screen.blit(text, (20, 20))

    def star_move(self):
        self.score += 1
        while 1:
            pos = (randint(1, 19), randint(1, 17))
            if self.is_free(pos):
                return pos

    # Создаем метод для получения тайла  (это нужно для случая смены карты)
    def get_tile_id(self, position):
        # print(self.map.tiledgidmap[self.map.get_tile_gid(*position, 0)])
        return self.map.tiledgidmap[self.map.get_tile_gid(*position, 0)]

    # Метод проверяет можно ли идти в данную клетку свободна ли она
    def is_free(self, position):
        # print(position)
        return self.get_tile_id(position) in self.free_tile

    # Метод разрабатывает путь (первый шаг) противника. Волновой алгоритм или алгоритм обхода в ширину
    def find_path_step(self, start, target):

        INF = 1000  # Константа условной бесконечности от точки старта
        x, y = start  # Координаты стартовой клетки
        distance = [[INF] * self.width for _ in range(self.height)]  # Расстояние до каждой клетки
        distance[y][x] = 0  # Расстояние до стартовой клетки равно 0.
        prev = [[None] * self.width for _ in range(self.height)]  # Вложенный список хранит предыдущие клетки
        queue = [(x, y)]  # Будем проверять в очереди все клетки
        while queue:  # Пока очередь не пуста
            x, y = queue.pop(0)  # Выбираем первый элемент из очереди
            for dx, dy in (1, 0), (0, 1), (-1, 0), (0, -1):  # Кортеж смещений
                next_x, next_y = x + dx, y + dy  # Это новые координаты
                if (0 < next_x < self.width and 0 < next_y < self.height and
                        self.is_free((next_x, next_y)) and distance[next_y][next_x] == INF):  # Если клетка
                    # в поле и по ней можно ходить и мы в ней ещё не были
                    distance[next_y][next_x] = distance[y][x] + 1  # Рассчитаем новое расстояние до клетки
                    prev[next_y][next_x] = (x, y)  # Текущая клетка уходит в предыдущую
                    queue.append((next_x, next_y))  # Добавляем новую клетку в очередь, чтобы потом её рассмотреть
        x, y = target
        if distance[y][x] == INF or start == target:  # Если расстояние до последней точки по прежнему равно INF
            # или стартовая клетка совпадает с конечной
            return start  # Тогда мы никуда не ходим а функция вернет стартовую клетку
        while prev[y][x] != start:  # Далее будем двигаться до тех пор пока не окажемся на клетке соседней стартовой
            x, y = prev[y][x]  # В кортеж помещаем предыдущую клетку
        return x, y  # В конце возвращаем ту клетку на которой остановились


class Hero:  # Класс героя исполнителя

    def __init__(self, position):
        self.x, self.y = position
        #self.image = pygame.image.load(f"images/{pic}")
        self.n = 0
        self.k = 0

    def get_position(self):
        return self.x, self.y

    def set_position(self, position):
        self.x, self.y = position

    def sprite_pic(self, k, n):

        self.k = k
        self.n = n


    def out_sprite_pic(self):
        return self.n

    # Метод рисования  - героя игры
    def render(self, screen):
        delta = (frames[self.k + self.n].get_width() - TILE_SIZE) // 2
        screen.blit(frames[self.k + self.n], ((self.x * TILE_SIZE - delta), (self.y * TILE_SIZE - delta)))


class Star:  # Класс звезды

    def __init__(self, position):
        self.x, self.y = position
        self.image = pygame.image.load(f"images/star.png")
        self.k = 0

    def get_position(self):
        return self.x, self.y

    def set_position(self, position):
        self.x, self.y = position

    # Метод рисования  - героя игры
    def render(self, screen):
        self.k += 1
        if self.k == 7:
            self.k = 0

        delta = (frames1[self.k].get_width() - TILE_SIZE) // 2
        screen.blit(frames1[self.k], (self.x * TILE_SIZE - delta, (self.y * TILE_SIZE - delta)))


class Enemy:  # Класс противника

    def __init__(self, pic, position):
        self.x, self.y = position
        self.delay = 400  # Задержка между срабатываниями таймера
        pygame.time.set_timer(ENEMY_EVENT_TYPE, self.delay)  # Установим таймер с задержкой времени
        self.image = pygame.image.load(f"images/{pic}")
        self.lird = 0
        self.spr_num = 0

    def get_position(self):
        #  print('+++', self.x, self.y)

        return self.x, self.y

    def set_position(self, position):
        if position[1] < self.y:
            self.lird = 12

        if position[1] > self.y:
            self.lird = 0
        if position[0] > self.x:
            self.lird = 8
        if position[0] < self.x:
            self.lird = 4
        self.spr_num += 1
        if self.spr_num == 4:
            self.spr_num = 0
        self.x, self.y = position


    # Метод рисования кружка - противника в игре
    def render(self, screen):

        delta = (frames2[self.lird + self.spr_num].get_width() - TILE_SIZE) // 2
        screen.blit(frames2[self.lird + self.spr_num], (self.x * TILE_SIZE - delta, (self.y * TILE_SIZE - delta)))


#  Класс для игры
class Game:

    def __init__(self, labyrinth, hero, enemy, star):
        self.labyrinth = labyrinth
        self.hero = hero
        self.enemy = enemy
        self.star = star
        # self.score = 0

    def render(self, screen):
        self.labyrinth.render(screen)
        self.hero.render(screen)
        self.enemy.render(screen)
        self.star.render(screen)

    # Метод проверяет нажата ли клавиша, если да, то меняем координаты героя
    def update_hero(self):
        next_x, next_y = self.hero.get_position()
        k_look = 0
        sprite_num = self.hero.out_sprite_pic()
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            next_x -= 1
            k_look = 8
            sprite_num += 1
            step_hero.play()
        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            next_x += 1
            k_look = 12
            sprite_num += 1
            step_hero.play()
        if pygame.key.get_pressed()[pygame.K_UP]:
            next_y -= 1
            k_look = 4
            sprite_num += 1
            step_hero.play()
        if pygame.key.get_pressed()[pygame.K_DOWN]:
            next_y += 1
            k_look = 0
            sprite_num += 1
            step_hero.play()
        if self.labyrinth.is_free((next_x, next_y)):
            self.hero.set_position((next_x, next_y))
            if sprite_num == 4:
                sprite_num = 0
            self.hero.sprite_pic(k_look, sprite_num)


    # Метод перемещения противника
    def move_enemy(self):  # Считает новые координаты и изменяет координаты противника
        next_position = self.labyrinth.find_path_step(self.enemy.get_position(), self.hero.get_position())
        self.enemy.set_position(next_position)
        step_enemy.play()

    # метод проверяет дошли ли мы до нужной клетки. Если да то мы выиграли
    def check_win(self):
        return self.labyrinth.get_tile_id(self.hero.get_position()) == self.labyrinth.finish_tile

    # Метод проверяет совпадают ли координаты у врага и у героя
    def check_lose(self):
        return self.hero.get_position() == self.enemy.get_position()

    def check_star(self):
        return self.hero.get_position() == self.star.get_position()


# Метод выводит сообщение о том, что мы выиграли
def show_message(screen, message):
    font = pygame.font.Font(None, 50)
    text = font.render(message, 1, (50, 70, 0))
    text_x = WINDOW_WIDTH // 2 - text.get_width() // 2
    text_y = WINDOW_HEIGHT // 2 - text.get_height() // 2
    text_w = text.get_width()
    text_h = text.get_height()
    pygame.draw.rect(screen, (200, 150, 50), (text_x - 10, text_y - 10, text_w + 20, text_h + 20))
    screen.blit(text, (text_x, text_y))


def main():
    pygame.init()  # Инициализируем pygame
    # Создаем окно для рисования
    pygame.display.set_caption('Догони!')
    screen = pygame.display.set_mode(WINDOW_SIZE)
    start_screen()

    # Создаем объект лабиринт экземпляр нашего класса
    labyrinth = Labyrinth("map2.tmx", [30, 46], 46)
    # Объект класса Героя с координатами в центре карты
    hero = Hero((10, 9))

    enemy = Enemy("enemy.png", (19, 9))

    star = Star((13, 9))

    # dragon = AnimatedSprite("pygame-8-1.png", 8, 2, 50, 50)

    # Объект класса Game
    # game = Game(labyrinth, hero, enemy, star)
    game = Game(labyrinth, hero, enemy, star)
    clock = pygame.time.Clock()  # Объект clock для поддержки данной частоты кадров
    running = True
    game_over = False  # Флаг для окончания игрового момента
    sound_fl = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # обавим обработку события, которое генерируется таймером
            if event.type == ENEMY_EVENT_TYPE and not game_over:
                game.move_enemy()
        # Проверяем нажата ли нужная клавиша в методе:
        if not game_over:
            game.update_hero()
        screen.fill((0, 0, 0))
        # Вызов метода render
        game.render(screen)
        if game.check_win():  # Проверяем если мы выиграли
            game_over = True
            #victory.play(0)
            show_message(screen, "Ура! Вы выиграли!!!")
            if sound_fl == 0:
                victory.play()
                sound_fl = 1

        if game.check_lose():  # Проверяем если мы проиграли
            game_over = True
            show_message(screen, "Увы. Вы проиграли.")
            if sound_fl == 0:
                game_ov.play()
                sound_fl = 1

        if game.check_star():  # Проверяем если звезд
            money.play()
            star.set_position(labyrinth.star_move())

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    frames = []  # Герой
    sprite = pygame.image.load("images/hero1.png").convert_alpha()
    width, height = sprite.get_size()
    w, h = width / 4, height / 4
    row = 0
    for j in range(int(height / h)):
        for i in range(int(width / w)):
            frames.append(sprite.subsurface(pygame.Rect(i * w, row, w, h)))
        row += int(h)

    frames1 = []  # Звезда (монета)
    sprite = pygame.image.load("images/cash.png").convert_alpha()
    width, height = sprite.get_size()
    w, h = width / 7, height
    for i in range(7):
        frames1.append(sprite.subsurface(pygame.Rect(w * i, 0, w, h)))

    frames2 = []  # Противник
    sprite = pygame.image.load("images/enemy1.png").convert_alpha()
    width, height = sprite.get_size()
    w, h = width / 4, height / 4
    row = 0
    for j in range(int(height / h)):
        for i in range(int(width / w)):
            frames2.append(sprite.subsurface(pygame.Rect(i * w, row, w, h)))
        row += int(h)

    main()

