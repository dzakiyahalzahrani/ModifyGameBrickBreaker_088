import tkinter as tk
import pygame


class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y, bounce_sound):
        self.radius = 10
        self.direction = [1, -1]
        self.speed = 5
        self.bounce_sound = bounce_sound
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='#FB9833')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
            self.bounce_sound.play()
        if coords[1] <= 0:
            self.direction[1] *= -1
            self.bounce_sound.play()
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()
                self.bounce_sound.play()
                return True
        return False


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#1B768E')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: '#FCEFEF', 2: '#4D555B', 3: '#FB9833'}

    def __init__(self, canvas, x, y, hits, color):
        self.width = 75
        self.height = 20
        self.hits = hits
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item,
                                   fill=Brick.COLORS[self.hits])


class Game(tk.Frame):
    def __init__(self, master, sounds):
        super(Game, self).__init__(master)
        self.lives = 3
        self.score = 0
        self.width = 610
        self.height = 400
        self.sounds = sounds
        self.canvas = tk.Canvas(self, bg='#012538',
                                width=self.width,
                                height=self.height)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 326)
        self.items[self.paddle.item] = self.paddle
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3, '#FB9833')
            self.add_brick(x + 37.5, 70, 2, '#4D555B')
            self.add_brick(x + 37.5, 90, 1, '#FCEFEF')

        self.hud = None
        self.hearts = []
        self.score_text = None
        self.setup_game()
        self.create_hearts()
        self.canvas.focus_set()
        self.canvas.bind('<Left>',
                         lambda _: self.paddle.move(-10))
        self.canvas.bind('<Right>',
                         lambda _: self.paddle.move(10))

    def setup_game(self):
        self.add_ball()
        self.update_hud()
        self.text = self.draw_text(self.width / 2, self.height / 2, 'Press Space to start', size=16)
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310, self.sounds['bounce'])
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits, color):
        brick = Brick(self.canvas, x, y, hits, color)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='12'):
        font = ('Verdana', size)
        return self.canvas.create_text(x, y, text=text,
                                       font=font, fill='white')

    def create_hearts(self):
        for i in range(3):
            heart = self.canvas.create_text(20 + i * 30, 20, text='❤',
                                            font=('Verdana', 20), fill='red')
            self.hearts.append(heart)

    def update_hud(self):
        if self.score_text is None:
            self.score_text = self.draw_text(550, 20, f'Score: {self.score}', size=12)
        else:
            self.canvas.itemconfig(self.score_text, text=f'Score: {self.score}')

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.ball.speed = None
            self.sounds['win'].play()
            self.draw_text(self.width / 2, self.height / 2, 'You Win!', size=20)
        elif self.ball.get_position()[3] >= self.height:
            self.ball.speed = None
            self.lives -= 1
            if self.lives < 0:
                self.show_game_over_screen()
            else:
                self.canvas.delete(self.hearts[self.lives])
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        if self.ball.collide(objects):
            self.score += 10
            self.update_hud()

    def show_game_over_screen(self):
        self.draw_text(self.width / 2, 150, 'Game Over!', size=20)
        self.sounds['lose'].play()

        # Center the Exit button
        button_width = 100
        button_height = 30
        btn_exit_x = (self.width - button_width) / 2
        btn_exit_y = self.height / 2

        btn_exit = tk.Button(self, text="Exit", command=self.quit_game)
        btn_exit.place(x=btn_exit_x, y=btn_exit_y, width=button_width, height=button_height)

    def quit_game(self):
        self.master.destroy()


if __name__ == '__main__':
    pygame.init()
    pygame.mixer.init()
    sounds = {
        'bounce': pygame.mixer.Sound('ball-bounce.mp3'),
        'win': pygame.mixer.Sound('game-win.mp3'),
        'lose': pygame.mixer.Sound('game-lose.mp3')
    }

    root = tk.Tk()
    root.title('Break those Bricks!')
    game = Game(root, sounds)
    game.mainloop()
