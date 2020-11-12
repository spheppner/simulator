"""
rocket simulation (nnt)

author: Simon Heppner
email: simon@heppner.at
website: simon.heppner.at
"""

import pygame
import pygame.freetype  # not automatically loaded when importing pygame!
import pygame.gfxdraw
import random
import math
import agent
from keras.models import load_model
import numpy as np
import time


class VectorSprite(pygame.sprite.Sprite):
    """base class for sprites. this class inherits from pygame sprite class"""

    number = 0  # unique number for each sprite

    # numbers = {} # { number, Sprite }

    def __init__(
        self,
        pos=None,
        move=None,
        _layer=0,
        angle=0,
        radius=0,
        color=(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        ),
        hitpoints=100,
        hitpointsfull=100,
        stop_on_edge=False,
        kill_on_edge=False,
        bounce_on_edge=False,
        warp_on_edge=False,
        age=0,
        max_age=None,
        max_distance=None,
        picture=None,
        boss=None,
        # kill_with_boss = False,
        move_with_boss=False,
        area=None,  # pygame.Rect
        **kwargs
    ):
        ### initialize pygame sprite DO NOT DELETE THIS LINE
        pygame.sprite.Sprite.__init__(self, self.groups)
        mylocals = locals().copy()  # copy locals() so that it does not updates itself
        for key in mylocals:
            if (
                key != "self" and key != "kwargs"
            ):  # iterate over all named arguments, including default values
                setattr(self, key, mylocals[key])
        for key, arg in kwargs.items():  # iterate over all **kwargs arguments
            setattr(self, key, arg)
        if pos is None:
            self.pos = pygame.math.Vector2(200, 200)
        if move is None:
            self.move = pygame.math.Vector2(0, 0)
        self._overwrite_parameters()

        self.number = VectorSprite.number  # unique number for each sprite
        VectorSprite.number += 1
        # VectorSprite.numbers[self.number] = self
        # self.visible = False
        self.create_image()
        self.distance_traveled = 0  # in pixel
        # self.rect.center = (-300,-300) # avoid blinking image in topleft corner
        if self.angle != 0:
            self.set_angle(self.angle)

    def _overwrite_parameters(self):
        """change parameters before create_image is called"""
        pass

    def _default_parameters(self, **kwargs):
        """get unlimited named arguments and turn them into attributes
        default values for missing keywords"""

        for key, arg in kwargs.items():
            setattr(self, key, arg)
        if "layer" not in kwargs:
            self.layer = 0
        # else:
        #    self.layer = self.layer
        if "pos" not in kwargs:
            self.pos = pygame.math.Vector2(200, 200)
        if "move" not in kwargs:
            self.move = pygame.math.Vector2(0, 0)
        if "angle" not in kwargs:
            self.angle = 0  # facing right?
        if "radius" not in kwargs:
            self.radius = 5
        # if "width" not in kwargs:
        #    self.width = self.radius * 2
        # if "height" not in kwargs:
        #    self.height = self.radius * 2
        if "color" not in kwargs:
            # self.color = None
            self.color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )
        if "hitpoints" not in kwargs:
            self.hitpoints = 100
        self.hitpointsfull = self.hitpoints  # makes a copy

        if "stop_on_edge" not in kwargs:
            self.stop_on_edge = False
        if "bounce_on_edge" not in kwargs:
            self.bounce_on_edge = False
        if "kill_on_edge" not in kwargs:
            self.kill_on_edge = False
        if "warp_on_edge" not in kwargs:
            self.warp_on_edge = False
        if "age" not in kwargs:
            self.age = 0  # age in seconds. A negative age means waiting time until sprite appears
        if "max_age" not in kwargs:
            self.max_age = None

        if "max_distance" not in kwargs:
            self.max_distance = None
        if "picture" not in kwargs:
            self.picture = None
        if "boss" not in kwargs:
            self.boss = None
        if "kill_with_boss" not in kwargs:
            self.kill_with_boss = False
        if "move_with_boss" not in kwargs:
            self.move_with_boss = False

    def kill(self):
        # check if this is a boss and kill all his underlings as well
        tokill = [s for s in Viewer.allgroup if "boss" in s.__dict__ and s.boss == self]
        # for s in Viewer.allgroup:
        #    if "boss" in s.__dict__ and s.boss == self:
        #        tokill.append(s)
        for s in tokill:
            s.kill()
        # if self.number in self.numbers:
        #   del VectorSprite.numbers[self.number] # remove Sprite from numbers dict
        pygame.sprite.Sprite.kill(self)

    def create_image(self):
        if self.picture is not None:
            self.image = self.picture.copy()
        else:
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(self.color)
        self.image = self.image.convert_alpha()
        self.image0 = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (round(self.pos[0], 0), round(self.pos[1], 0))
        # self.width = self.rect.width
        # self.height = self.rect.height

    def rotate(self, by_degree):
        """rotates a sprite and changes it's angle by by_degree"""
        self.angle += by_degree
        self.angle = self.angle % 360
        oldcenter = self.rect.center
        self.image = pygame.transform.rotate(self.image0, -self.angle)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = oldcenter

    def get_angle(self):
        if self.angle > 180:
            return self.angle - 360
        return self.angle

    def set_angle(self, degree):
        """rotates a sprite and changes it's angle to degree"""
        self.angle = degree
        self.angle = self.angle % 360
        oldcenter = self.rect.center
        self.image = pygame.transform.rotate(self.image0, -self.angle)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = oldcenter

    def update(self, seconds):
        """calculate movement, position and bouncing on edge"""
        self.age += seconds
        if self.age < 0:
            return
        # self.visible = True
        self.distance_traveled += self.move.length() * seconds
        # ----- kill because... ------
        if self.hitpoints <= 0:
            self.kill()
        if self.max_age is not None and self.age > self.max_age:
            self.kill()
        if self.max_distance is not None and self.distance_traveled > self.max_distance:
            self.kill()
        # ---- movement with/without boss ----
        if self.boss and self.move_with_boss:
            self.pos = self.boss.pos
            self.move = self.boss.move
        else:
            # move independent of boss
            self.pos += self.move * seconds
            self.wallcheck()
        # print("rect:", self.pos.x, self.pos.y)
        self.rect.center = (int(round(self.pos.x, 0)), int(round(self.pos.y, 0)))

    def wallcheck(self):
        # ---- bounce / kill on screen edge ----
        if self.area is None:
            self.area = Viewer.screenrect
            # print(self.area)
        # ------- left edge ----
        if self.pos.x < self.area.left:
            if self.stop_on_edge:
                self.pos.x = self.area.left
            if self.kill_on_edge:
                self.kill()
            if self.bounce_on_edge:
                self.pos.x = self.area.left
                self.move.x *= -1
            if self.warp_on_edge:
                self.pos.x = self.area.right
        # -------- upper edge -----
        if self.pos.y < self.area.top:
            if self.stop_on_edge:
                self.pos.y = self.area.top
            if self.kill_on_edge:
                self.kill()
            if self.bounce_on_edge:
                self.pos.y = self.area.top
                self.move.y *= -1
            if self.warp_on_edge:
                self.pos.y = self.area.bottom
        # -------- right edge -----
        if self.pos.x > self.area.right:
            if self.stop_on_edge:
                self.pos.x = self.area.right
            if self.kill_on_edge:
                self.kill()
            if self.bounce_on_edge:
                self.pos.x = self.area.right
                self.move.x *= -1
            if self.warp_on_edge:
                self.pos.x = self.area.left
        # --------- lower edge ------------
        if self.pos.y > self.area.bottom:
            if self.stop_on_edge:
                self.pos.y = self.area.bottom
            if self.kill_on_edge:
                self.kill()
            if self.bounce_on_edge:
                self.pos.y = self.area.bottom
                self.move.y *= -1
            if self.warp_on_edge:
                self.pos.y = self.area.top


class Crosshair(VectorSprite):
    def create_image(self):
        self.image = pygame.Surface((100, 100))
        for radius in (5, 10, 15, 20, 25, 30):
            pygame.draw.circle(self.image, (50, 50, 50), (50, 50), 50 - radius, 1)
        pygame.draw.line(self.image, (200, 0, 0), (0, 0), (100, 100), 2)
        pygame.draw.line(self.image, (200, 0, 0), (100, 0), (0, 100), 2)
        pygame.draw.circle(self.image, (0, 0, 0), (50, 50), 15)
        self.image.set_colorkey((0, 0, 0))
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = pygame.mouse.get_pos()

    def update(self, seconds):
        self.pos = pygame.math.Vector2(pygame.mouse.get_pos())
        super().update(seconds)


class PredCrosshair(VectorSprite):
    def create_image(self):
        self.image = pygame.Surface((100, 100))
        for radius in (5, 10, 15, 20, 25, 30):
            pygame.draw.circle(self.image, (50, 255, 50), (50, 50), 50 - radius, 1)
        pygame.draw.line(self.image, (0, 255, 0), (0, 0), (100, 100), 2)
        pygame.draw.line(self.image, (0, 255, 0), (100, 0), (0, 100), 2)
        pygame.draw.circle(self.image, (0, 0, 0), (50, 50), 15)
        self.image.set_colorkey((0, 0, 0))
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = pygame.math.Vector2(50, 50)

    def update(self, seconds, agent=None, targetpos=None, direction=0, tspeed=(0,50), pspeed=(0,200)):
        if agent != None:
            if targetpos != None:
                prediction = round(
                    agent.model.predict(
                        np.array(
                            [
                                [
                                    round(tspeed[1]),
                                    round(pspeed[1]),
                                    int(targetpos.y),
                                    direction,

                                ]
                            ],
                            dtype=np.float32,
                        )
                    )[0][0]
                )
                self.pos = pygame.math.Vector2(800, prediction)
        super().update(seconds)


class Flytext(VectorSprite):
    def __init__(
        self,
        pos=pygame.math.Vector2(50, 50),
        move=pygame.math.Vector2(0, -50),
        text="hallo",
        color=(255, 0, 0),
        bgcolor=None,
        max_age=0.5,
        age=0,
        acceleration_factor=1.0,
        fontsize=48,
        textrotation=0,
        style=pygame.freetype.STYLE_STRONG,
        alpha_start=255,
        alpha_end=255,
        width_start=None,
        width_end=None,
        height_start=None,
        height_end=None,
        rotate_start=0,
        rotate_end=0,
        picture=None,
        _layer=7,
    ):
        """Create a flying VectorSprite with text or picture that disappears after a while

        :param pygame.math.Vector2 pos:     startposition in Pixel. To attach the text to another Sprite, use an existing Vector.
        :param pygame.math.Vector2 move:    movevector in Pixel per second
        :param text:                        the text to render. accept unicode chars. Will be overwritten when picture is given
        :param (int,int,int) color:         foregroundcolor for text
        :param (int,int,int) bgcolor:       backgroundcolor for text. If set to None, black is the transparent color
        :param float max_age:               lifetime of Flytext in seconds. Delete itself when age > max_age
        :param float age:                   start age in seconds. If negative, Flytext stay invisible until age >= 0
        :param float acceleration_factor:   1.0 for no acceleration. > 1 for acceleration of move Vector, < 1 for negative acceleration
        :param int fontsize:                fontsize for text
        :param float textrotation:          static textrotation in degree for rendering text.
        :param int style:                   effect for text rendering, see pygame.freetype constants
        :param int alpha_start:             alpha value for age =0. 255 is no transparency, 0 is full transparent
        :param int alpha_end:               alpha value for age = max_age.
        :param int width_start:             start value for dynamic zooming of width in pixel
        :param int width_end:               end value for dynamic zooming of width in pixel
        :param int height_start:            start value for dynamic zooming of height in pixel
        :param int height_end:              end value for dynamic zooming of height in pixel
        :param float rotate_start:          start angle for dynamic rotation of the whole Flytext Sprite
        :param float rotate_end:            end angle for dynamic rotation
        :param picture:                     a picture object. If not None, it overwrites any given text
        :return: None
        """

        self.recalc_each_frame = False
        self.text = text
        self.alpha_start = alpha_start
        self.alpha_end = alpha_end
        self.alpha_diff_per_second = (alpha_start - alpha_end) / max_age
        if alpha_end != alpha_start:
            self.recalc_each_frame = True
        self.style = style
        self.acceleration_factor = acceleration_factor
        self.fontsize = fontsize
        self.textrotation = textrotation
        self.color = color
        self.bgcolor = bgcolor
        self.width_start = width_start
        self.width_end = width_end
        self.height_start = height_start
        self.height_end = height_end
        self.picture = picture
        # print( "my picture is:", self.picture)
        if width_start is not None:
            self.width_diff_per_second = (width_end - width_start) / max_age
            self.recalc_each_frame = True
        else:
            self.width_diff_per_second = 0
        if height_start is not None:
            self.height_diff_per_second = (height_end - height_start) / max_age
            self.recalc_each_frame = True
        else:
            self.height_diff_per_second = 0
        self.rotate_start = rotate_start
        self.rotate_end = rotate_end
        if (rotate_start != 0 or rotate_end != 0) and rotate_start != rotate_end:
            self.rotate_diff_per_second = (rotate_end - rotate_start) / max_age
            self.recalc_each_frame = True
        else:
            self.rotate_diff_per_second = 0
        # self.visible = False
        VectorSprite.__init__(
            self,
            color=color,
            pos=pos,
            move=move,
            max_age=max_age,
            age=age,
            picture=picture,
        )
        # self._layer = 7  # order of sprite layers (before / behind other sprites)
        # acceleration_factor  # if < 1, Text moves slower. if > 1, text moves faster.

    def create_image(self):
        if self.picture is not None:
            # print("picture", self)
            self.image = self.picture
        else:
            # print("no picture", self)
            myfont = Viewer.font
            # text, textrect = myfont.render(
            # fgcolor=self.color,
            # bgcolor=self.bgcolor,
            # get_rect(text, style=STYLE_DEFAULT, rotation=0, size=0) -> rect
            textrect = myfont.get_rect(
                text=self.text,
                size=self.fontsize,
                rotation=self.textrotation,
                style=self.style,
            )  # font 22
            self.image = pygame.Surface((textrect.width, textrect.height))
            # render_to(surf, dest, text, fgcolor=None, bgcolor=None, style=STYLE_DEFAULT, rotation=0, size=0) -> Rect
            textrect = myfont.render_to(
                surf=self.image,
                dest=(0, 0),
                text=self.text,
                fgcolor=self.color,
                bgcolor=self.bgcolor,
                style=self.style,
                rotation=self.textrotation,
                size=self.fontsize,
            )
            if self.bgcolor is None:
                self.image.set_colorkey((0, 0, 0))

            self.rect = textrect
            # picture ? overwrites text

        # transparent ?
        if self.alpha_start == self.alpha_end == 255:
            pass
        elif self.alpha_start == self.alpha_end:
            self.image.set_alpha(self.alpha_start)
            # print("fix alpha", self.alpha_start)
        else:
            self.image.set_alpha(
                self.alpha_start - self.age * self.alpha_diff_per_second
            )
            # print("alpha:", self.alpha_start - self.age * self.alpha_diff_per_second)
        self.image.convert_alpha()
        # save the rect center for zooming and rotating
        oldcenter = self.image.get_rect().center
        # dynamic zooming ?
        if self.width_start is not None or self.height_start is not None:
            if self.width_start is None:
                self.width_start = textrect.width
            if self.height_start is None:
                self.height_start = textrect.height
            w = self.width_start + self.age * self.width_diff_per_second
            h = self.height_start + self.age * self.height_diff_per_second
            self.image = pygame.transform.scale(self.image, (int(w), int(h)))
        # rotation?
        if self.rotate_start != 0 or self.rotate_end != 0:
            if self.rotate_diff_per_second == 0:
                self.image = pygame.transform.rotate(self.image, self.rotate_start)
            else:
                self.image = pygame.transform.rotate(
                    self.image,
                    self.rotate_start + self.age * self.rotate_diff_per_second,
                )
        # restore the old center after zooming and rotating
        self.rect = self.image.get_rect()
        self.rect.center = oldcenter
        self.rect.center = (int(round(self.pos.x, 0)), int(round(self.pos.y, 0)))

    def update(self, seconds):
        VectorSprite.update(self, seconds)
        if self.age < 0:
            return
        self.move *= self.acceleration_factor
        if self.recalc_each_frame:
            self.create_image()


class Beam(VectorSprite):
    """a glowing laser beam"""

    width = 25  # must be >= 10
    height = 5
    speed = 99
    damage = 1

    def _overwrite_parameters(self):
        self.kill_on_edge = True
        # self.color = randomize_colors(self.color, 50)

    def create_image(self):
        r, g, b = randomize_colors(self.color, 50)
        self.image = pygame.Surface((self.width, self.height))
        pygame.gfxdraw.filled_polygon(
            self.image,
            (
                (0, self.height // 2),
                (self.width * 0.9, 0),
                (self.width, self.height // 2),
                (self.width * 0.9, self.height),
            ),
            (r, g, b),
        )
        self.image.set_colorkey((0, 0, 0))
        self.image.convert_alpha()
        self.image = pygame.transform.rotate(self.image, 180)
        self.image0 = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = int(self.pos.x), int(self.pos.y)
        self.set_angle(self.angle)


class Rocket(Beam):
    """like a Beam, but tumbles in flight """

    width = 10  # must be >= 10
    height = 5
    speed = 44
    damage = 50
    color = (100, 45, 56)

    def update(self, seconds):
        # self.create_image()
        super().update(seconds)
        if random.random() < 0.7:
            Smoke(pos=pygame.math.Vector2(self.pos.x, self.pos.y))
        # tumble
        # if random.random() < 0.1:
        delta_angle = random.choice((-3, -2, -1, 0, 0, 0, 0, 0, 0, 1, 2, 3))
        self.move.rotate_ip(delta_angle)
        self.rotate(delta_angle)


class SmarterRocket(Beam):

    def _overwrite_parameters(self):
        self.speed = (0,200)
        self.targetSpeed = (0,50)

    def kill(self, winner=False, writeData=False, tspeed=None):
        if tspeed != None:
            self.targetSpeed = tspeed
        if winner:
            if writeData:
                with open("movingdataset.txt", "a") as dataset:
                    dataset.write(
                        str(int(self.targetSpeed[1]))
                        + ","
                        + str(self.speed[1])
                        + ","
                        + str(int(self.moving_target_pos[1]))
                        + ","
                        + str(self.direction)
                        + ","
                        + str(int(self.target[1]))
                        + "\n"
                    )
        super().kill()

class SmartRocket(Rocket):
    def _overwrite_parameters(self):
        self.kill_on_edge = True
        self.move = pygame.math.Vector2(50, 0)
        self.pos = pygame.math.Vector2(50, 400)
        self.factor1 = 0.1 + random.random() * 5.5
        self.factor2 = 5.0 + random.random() * 60
        self.factor3 = random.choice((-1, 1))
        self.factor4 = random.choice((-1, 1))
        self.writeData = False
        self.smokeToggle = True
        self.target = (200, Viewer.height - 200, 800)

    def update_old(self, seconds):
        """calculate movement, position and bouncing on edge"""
        self.age += seconds
        if self.age < 0:
            return
        # self.visible = True
        self.distance_traveled += self.move.length() * seconds
        # ----- kill because... ------
        if self.hitpoints <= 0:
            self.kill()
        if self.max_age is not None and self.age > self.max_age:
            self.kill()
        if self.max_distance is not None and self.distance_traveled > self.max_distance:
            self.kill()
        # ---- movement with/without boss ----
        if self.boss and self.move_with_boss:
            self.pos = self.boss.pos
            self.move = self.boss.move
        else:
            # move independent of boss
            self.pos += self.move * seconds
            self.wallcheck()
        # print("rect:", self.pos.x, self.pos.y)
        self.rect.center = (int(round(self.pos.x, 0)), int(round(self.pos.y, 0)))

    def update(self, seconds):
        self.create_image()
        self.update_old(seconds)
        if self.smokeToggle:
            if random.random() < 0.7:
                Smoke(pos=pygame.math.Vector2(self.pos.x, self.pos.y), color=self.color)
        # tumble
        # if random.random() < 0.1:
        # delta_angle = random.choice((-3,-2,-1,0,0,0,0,0,0,1,2,3))
        delta_angle = (
            math.sin(self.age * self.factor1 * self.factor3)
            * self.factor2
            * self.factor4
        )
        self.move.rotate_ip(delta_angle * seconds)
        self.rotate(delta_angle * seconds)
        if (
            self.pos.x > self.target[2]
            and self.pos.y > self.target[0]
            and self.pos.y < self.target[1]
        ):
            winner = 1
            self.kill(winner, True)
        if self.pos.x > self.target[2] and (
            self.pos.y < self.target[0] or self.pos.y > self.target[1]
        ):
            winner = 0
            self.kill(winner, True)
        self.setColor(self.color)

    def setColor(self, color):
        self.color = color

    def kill(self, winner=0, sparks=False):
        if self.writeData:
            with open("dataset.txt", "a") as dataset:
                dataset.write(
                    str(round(self.factor1, 1))
                    + ","
                    + str(round(self.factor2, 1))
                    + ","
                    + str(round(self.factor3, 1))
                    + ","
                    + str(round(self.factor4, 1))
                    + ","
                    + str(winner)
                    + "\n"
                )
        if sparks:
            Explosion(pos=self.pos, color=self.color, maxduration=0.5, sparksmax=5)
        super().kill()


class Spark(VectorSprite):
    def _overwrite_parameters(self):
        self._layer = 9
        self.kill_on_edge = True
        self.color = randomize_colors(self.color, 50)

    def create_image(self):
        self.image = pygame.Surface((10, 10))
        pygame.draw.line(self.image, self.color, (10, 5), (5, 5), 3)
        pygame.draw.line(self.image, self.color, (5, 5), (2, 5), 1)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.image0 = self.image.copy()


class Explosion:
    def __init__(
        self,
        pos,
        maxspeed=150,
        minspeed=20,
        color=(255, 255, 0),
        maxduration=2.5,
        gravityy=3.7,
        sparksmin=5,
        sparksmax=20,
        a1=0,
        a2=360,
    ):
        for s in range(random.randint(sparksmin, sparksmax)):
            v = pygame.math.Vector2(1, 0)  # vector aiming right (0°)
            a = random.triangular(a1, a2)
            v.rotate_ip(a)
            g = pygame.math.Vector2(0, -gravityy)
            speed = random.randint(minspeed, maxspeed)  # 150
            duration = random.random() * maxduration
            Spark(
                pos=pygame.math.Vector2(pos.x, pos.y),
                angle=a,
                move=v * speed,
                max_age=duration,
                color=color,
                gravity=g,
            )


class MovingTarget(VectorSprite):
    def _overwrite_parameters(self):
        self.bounce_on_edge = True

    def create_image(self):
        self.image = pygame.Surface((50, 50))
        self.image.fill(self.color)
        pygame.draw.rect(self.image, (50, 50, 50), (0, 0, 50, 50), 3)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = self.pos.x, self.pos.y

class Smoke(VectorSprite):
    """a round fragment or bubble particle, fading out"""

    def _overwrite_parameters(self):
        # self.speed = random.randint(10, 50)
        self.start_radius = 1

        self.radius = 1
        self.end_radius = 10  # random.randint(15,20)
        # if self.max_age is None:
        self.max_age = 7.5  # + random.random() * 2.5
        self.kill_on_edge = True
        self.kill_with_boss = False  # VERY IMPORTANT!!!
        # if self.move == pygame.math.Vector2(0, 0):
        #    self.move = pygame.math.Vector2(1, 0)
        #    self.move *= self.speed
        #    a, b = 0, 360
        #    self.move.rotate_ip(random.randint(a, b))
        self.alpha_start = 64
        self.alpha_end = 0
        self.alpha_diff_per_second = (self.alpha_start - self.alpha_end) / self.max_age
        # self.color = (10, 10, 10)
        # self.color = randomize_colors(color=self.color, by=35)

    def create_image(self):
        # self.radius = self.start_radius +
        self.image = pygame.Surface((2 * self.radius, 2 * self.radius))
        pygame.draw.circle(
            self.image, self.color, (self.radius, self.radius), self.radius
        )
        self.image.set_colorkey((0, 0, 0))
        self.image.set_alpha(self.alpha_start - self.age * self.alpha_diff_per_second)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = int(round(self.pos.x, 0)), int(round(self.pos.y, 0))
        # self.rect.center=(int(round(self.pos[0],0)), int(round(self.pos[1],0)))

    def update(self, seconds):
        # self.create_image()
        self.radius = (self.end_radius / self.max_age) * self.age
        self.radius = int(round(self.radius, 0))
        self.create_image()
        self.move = Viewer.windvector * seconds
        super().update(seconds)
        self.image.set_alpha(self.alpha_start - self.age * self.alpha_diff_per_second)
        self.image.convert_alpha()


class Viewer:
    width = 0
    height = 0
    screenrect = None
    font = None
    points = []
    windvector = None
    maxwind = 400
    spawn_rect_width = (
        40  # width of rects around topleft screencorner where new ships can spawn
    )
    menuitems = ["Static-Target Rockets", "Moving-Target Rockets", "Quit"]
    cursorindex = 0

    # playergroup = None # pygame sprite Group only for players

    def __init__(
        self,
        width=800,
        height=600,
    ):

        Viewer.width = width
        Viewer.height = height
        Viewer.screenrect = pygame.Rect(0, 0, width, height)
        Viewer.points = [(100, 100), (width - 50, height - 50)]
        Viewer.windvector = pygame.math.Vector2()
        Viewer.windvector.from_polar((random.randint(50, 250), random.randint(0, 360)))
        # first spwanrect is nort-east of topleft screencorner
        self.spawnrects = [
            pygame.Rect(
                -self.spawn_rect_width,
                -self.spawn_rect_width,
                self.spawn_rect_width,
                self.spawn_rect_width,
            )
        ]
        # create 4 additional spawnrects north of topleft screen corner
        for x in range(0, self.spawn_rect_width * 4 + 1, self.spawn_rect_width):
            self.spawnrects.append(
                pygame.Rect(
                    x,
                    -self.spawn_rect_width,
                    self.spawn_rect_width,
                    self.spawn_rect_width,
                )
            )
        # create 4 additional spawnrects west of topleft screen corner
        for y in range(0, self.spawn_rect_width * 4 + 1, self.spawn_rect_width):
            self.spawnrects.append(
                pygame.Rect(
                    -self.spawn_rect_width,
                    y,
                    self.spawn_rect_width,
                    self.spawn_rect_width,
                )
            )

        # ---- pygame init
        pygame.init()
        # pygame.mixer.init(11025) # raises exception on fail
        # Viewer.font = pygame.font.Font(os.path.join("data", "FreeMonoBold.otf"),26)
        # fontfile = os.path.join("data", "fonts", "DejaVuSans.ttf")
        # --- font ----
        # if you have your own font:
        # Viewer.font = pygame.freetype.Font(os.path.join("data","fonts","INSERT_YOUR_FONTFILENAME.ttf"))
        # otherwise:
        fontname = pygame.freetype.get_default_font()
        Viewer.font = pygame.freetype.SysFont(fontname, 64)

        # ------ joysticks init ----
        pygame.joystick.init()
        self.joysticks = [
            pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
        ]
        for j in self.joysticks:
            j.init()
        self.screen = pygame.display.set_mode(
            (self.width, self.height), pygame.DOUBLEBUF
        )
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.playtime = 0.0

        # ------ background images ------
        # self.backgroundfilenames = []  # every .jpg or .jpeg file in the folder 'data'
        # self.make_background()
        # self.load_images()

        self.prepare_sprites()
        self.setup()
        self.menuRun()

    def setup(self):
        self.icon = pygame.image.load("icon.png")

        self.background = pygame.Surface((Viewer.width, Viewer.height))
        self.background.fill((255, 255, 255))

        self.trained_agent = agent.TrainedAgent(actions=[0, 1])
        # X, Y = agent.loaddataset("dataset.txt", 4)
        # self.trained_agent.train(X, Y, savemodel=True)
        model = load_model("model.h5")
        self.trained_agent.loadmodel(model)

        self.movingAgent = agent.EvolvedAgent(actions=[0])
        X, Y = agent.loaddataset("movingdataset.txt", 4)
        self.movingAgent.train(X, Y, savemodel=True)
        #model = load_model("movingmodel.h5")
        #self.movingAgent.loadmodel(model)

    def prepare_sprites(self):
        """painting on the surface and create sprites"""
        Viewer.allgroup = pygame.sprite.LayeredUpdates()  # for drawing with layers
        Viewer.beamgroup = pygame.sprite.Group()
        Viewer.targetgroup = pygame.sprite.Group()
        # assign classes to groups
        VectorSprite.groups = self.allgroup
        Beam.groups = self.allgroup, self.beamgroup
        SmarterRocket.groups = self.allgroup, self.beamgroup
        Spark.groups = self.allgroup
        MovingTarget.groups = self.allgroup, self.targetgroup

        # Bubble.groups = self.allgroup, self.fxgroup  # special effects
        # Flytext.groups = self.allgroup, self.flytextgroup, self.flygroup
        # self.ship1 = Ship(pos=pygame.math.Vector2(400, 200), color=(0,0,200))
        # self.ship2 = Ship2(pos=pygame.math.Vector2(100, 100), color=(200,0,0))
        # self.ship3 = Ship3(pos=pygame.math.Vector2(100, 400), color=(0,200,0))
        # self.cannon1 = Cannon(pos=pygame.math.Vector2(300,400), color=(50,100,100))
        # self.cannon2 = Cannon(pos=pygame.math.Vector2(600,500), color=(50,100,100))

    def change_wind(self):
        # get length (radius) and angle from windvector
        r, a = Viewer.windvector.as_polar()
        delta_r = random.choice(
            (
                -3,
                -2,
                -2,
                -1,
                -1,
                -1,
                -1,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                1,
                1,
                1,
                1,
                1,
                2,
                2,
                3,
            )
        )
        delta_a = random.choice(
            (
                -3,
                -2,
                -2,
                -2,
                -1,
                -1,
                -1,
                -1,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                1,
                1,
                1,
                1,
                2,
                2,
                2,
                3,
            )
        )
        r = between(r + delta_r, 0, Viewer.maxwind)
        a = (a + delta_a) % 360
        Viewer.windvector.from_polar((r, a))
        # --- draw windrose ---
        write(
            self.screen,
            "wind: {:.0f} pixel/sec,  {:.0f}° ".format(r, 360 - a),
            x=5,
            y=Viewer.height - 115,
            color=(128, 128, 128),
            font_size=12,
        )
        pygame.draw.circle(
            self.screen, (128, 128, 128), (50, Viewer.height - 50), 50, 1
        )
        # ---- calculate wind triangle -----
        p0 = pygame.math.Vector2(50, Viewer.height - 50)  # center of circle
        p1 = pygame.math.Vector2()
        p1.from_polar((50, a))  # - a so that ° goes counterclockwise
        p1 = p0 + p1  # tip of triangle
        p2 = pygame.math.Vector2()
        p2.from_polar((50, a + 120))
        p3 = pygame.math.Vector2()
        p3.from_polar((50, a - 120))
        p2 = p0 + p2
        p3 = p0 + p3
        c = int(round(r / Viewer.maxwind * 255, 0))
        pygame.draw.polygon(
            self.screen,
            (c, c, c),
            [(int(round(p.x, 0)), int(round(p.y, 0))) for p in (p0, p2, p1, p3)],
            5,
        )
        # p4 = p0 - p1
        # pygame.draw.circle(self.screen, (200,0,0), (int(p1.x), int(p1.y)), 5)
        # p5 = pygame.math.Vector2()
        # p5.from_polar((windpercent, a))
        # p5 = p4 + p5
        # pygame.draw.line(self.screen, (64,64,64), (int(round(p4.x,0)), int(round(p4.y,0))), (int(round(p5.x,0)), int(round(p5.y,0))), 10)

    def menuRun(self):
        running = True
        while running:
            pressed_keys = pygame.key.get_pressed()
            milliseconds = self.clock.tick(self.fps)  #
            seconds = milliseconds / 1000
            # -------- events ------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # ------- pressed and released key ------
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key == pygame.K_UP:
                        if Viewer.cursorindex > 0:
                            Viewer.cursorindex -= 1
                    if event.key == pygame.K_DOWN:
                        if Viewer.cursorindex < len(Viewer.menuitems) - 1:
                            Viewer.cursorindex += 1
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        activeitem = Viewer.menuitems[Viewer.cursorindex]
                        if activeitem == "Static-Target Rockets":
                            self.menu_active = False
                            self.staticTargetRun()
                        elif activeitem == "Moving-Target Rockets":
                            self.menu_active = False
                            self.movingTargetRun()
                        elif activeitem == "Quit":
                            return

            # ---------- clear all --------------
            pygame.display.set_caption("Rocket Simulator | Menu")
            pygame.display.set_icon(self.icon)
            self.screen.blit(self.background, (0, 0))

            # ----------- writing on screen ----------
            for y, i in enumerate(Viewer.menuitems):
                write(
                    self.screen,
                    i,
                    Viewer.width // 2 - 100,
                    320 + y * 40,
                    color=(0, 0, 0),
                    font_size=40,
                )
            write(
                self.screen,
                "-->",
                Viewer.width // 2 - 185,
                320 + Viewer.cursorindex * 40,
                color=(0, 0, random.randint(200, 255)),
                font_size=40,
            )

            # --------- update all sprites ----------------
            self.allgroup.update(seconds)

            # ---------- blit all sprites --------------
            self.allgroup.draw(self.screen)
            pygame.display.flip()
        return

    def staticTargetRun(self):
        """The mainloop"""
        running = True

        # pygame.mouse.set_visible(False)
        click_oldleft, click_oldmiddle, click_oldright = False, False, False
        for _ in self.allgroup:
            _.kill()
        # points = []
        # --------------------------- main loop --------------------------
        while running:
            milliseconds = self.clock.tick(self.fps)  #
            seconds = milliseconds / 1000
            self.playtime += seconds
            # -------- events ------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # ------- pressed and released key ------
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key == pygame.K_SPACE:
                        for _ in range(5):
                            rocket = SmartRocket(
                                pos=pygame.math.Vector2(100, 400),
                                move=pygame.math.Vector2(50, 0),
                                angle=0,
                                kill_on_edge=True,
                                max_distance=2 * Viewer.width,
                                color=(0, 0, 0),
                            )
                            rocket.writeData = False
                            rocket.target = (200, Viewer.height - 200, 800)
                            rocket.smokeToggle = False
                            # featureString = str(round(rocket.factor1, 1)) + "," + str(round(rocket.factor2, 1)) + "," + str(round(rocket.factor3, 1)) + "," + str(round(rocket.factor4, 1))
                            prediction = round(
                                self.trained_agent.model.predict(
                                    np.array(
                                        [
                                            [
                                                round(rocket.factor1, 1),
                                                round(rocket.factor2, 1),
                                                round(rocket.factor3, 1),
                                                round(rocket.factor4, 1),
                                            ]
                                        ],
                                        dtype=np.float32,
                                    )
                                )[0][0]
                            )
                            if prediction == 1:
                                rocket.color = (0, 255, 0)
                            else:
                                rocket.color = (255, 0, 0)

                    if event.key == pygame.K_a:
                        i = 0
                        while i < 5:
                            rocket = SmartRocket(
                                pos=pygame.math.Vector2(100, 400),
                                move=pygame.math.Vector2(50, 0),
                                angle=0,
                                kill_on_edge=True,
                                max_distance=2 * Viewer.width,
                                color=(0, 0, 0),
                            )
                            rocket.writeData = False
                            rocket.target = (200, Viewer.height - 200, 800)
                            rocket.smokeToggle = False
                            # featureString = str(round(rocket.factor1, 1)) + "," + str(round(rocket.factor2, 1)) + "," + str(round(rocket.factor3, 1)) + "," + str(round(rocket.factor4, 1))
                            prediction = round(
                                self.trained_agent.model.predict(
                                    np.array(
                                        [
                                            [
                                                round(rocket.factor1, 1),
                                                round(rocket.factor2, 1),
                                                round(rocket.factor3, 1),
                                                round(rocket.factor4, 1),
                                            ]
                                        ],
                                        dtype=np.float32,
                                    )
                                )[0][0]
                            )
                            if prediction == 1:
                                rocket.color = (0, 255, 0)
                                i += 1
                            else:
                                rocket.kill(sparks=False)

                    if event.key == pygame.K_b:
                        i = 0
                        while i < 5:
                            rocket = SmartRocket(
                                pos=pygame.math.Vector2(100, 400),
                                move=pygame.math.Vector2(50, 0),
                                angle=0,
                                kill_on_edge=True,
                                max_distance=2 * Viewer.width,
                                color=(0, 0, 0),
                            )
                            rocket.writeData = False
                            rocket.target = (200, Viewer.height - 200, 800)
                            rocket.smokeToggle = False
                            # featureString = str(round(rocket.factor1, 1)) + "," + str(round(rocket.factor2, 1)) + "," + str(round(rocket.factor3, 1)) + "," + str(round(rocket.factor4, 1))
                            prediction = round(
                                self.trained_agent.model.predict(
                                    np.array(
                                        [
                                            [
                                                round(rocket.factor1, 1),
                                                round(rocket.factor2, 1),
                                                round(rocket.factor3, 1),
                                                round(rocket.factor4, 1),
                                            ]
                                        ],
                                        dtype=np.float32,
                                    )
                                )[0][0]
                            )
                            if prediction == 1:
                                rocket.kill(sparks=False)
                            else:
                                rocket.color = (255, 0, 0)
                                i += 1

            # ------------ pressed keys ------
            pressed_keys = pygame.key.get_pressed()
            # ///

            # ---------- clear all --------------
            pygame.display.set_caption("Rocket Simulator | Static-Target")
            pygame.display.set_icon(self.icon)
            self.screen.blit(self.background, (0, 0))

            # ----------- writing on screen ----------
            write(
                self.screen,
                "FPS: {:6.3}".format(self.clock.get_fps()),
                50,
                50,
                (0, 0, 250),
                20,
            )

            pygame.draw.line(
                self.background, (0, 0, 255), (800, 200), (800, Viewer.height - 200)
            )

            # --------- update all sprites ----------------
            self.allgroup.update(seconds)

            # ---------- blit all sprites --------------
            self.allgroup.draw(self.screen)
            pygame.display.flip()

        pygame.mouse.set_visible(True)
        pygame.quit()
        # try:
        #    sys.exit()
        # finally:
        #    pygame.quit()

    def movingTargetRun(self):
        """The mainloop"""
        running = True
        for _ in self.allgroup:
            _.kill()
        self.target1 = MovingTarget(
            pos=pygame.math.Vector2(800, 100), move=pygame.math.Vector2(0, 50)
        )
        self.start = pygame.math.Vector2(100, 400)
        self.crosshair = Crosshair()
        self.predicted_crosshair = PredCrosshair()
        pygame.mouse.set_visible(False)
        click_oldleft, click_oldmiddle, click_oldright = False, False, False
        # points = []
        # --------------------------- main loop --------------------------
        while running:
            milliseconds = self.clock.tick(self.fps)  #
            seconds = milliseconds / 1000
            self.playtime += seconds
            # -------- events ------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    target = pygame.math.Vector2(pygame.mouse.get_pos())

                    move = target - self.start
                    move.normalize_ip()
                    move *= 200
                    a = move.angle_to(pygame.math.Vector2(1, 0))
                    rocket = SmarterRocket(
                        pos=pygame.math.Vector2(100, 400),
                        move=move,
                        angle=-a,
                        kill_on_edge=True,
                        color=(0, 0, 0),
                        moving_target_pos = (self.target1.pos.x, self.target1.pos.y),
                        target = (target.x, target.y),
                        direction = 1 if self.target1.move.y > 0 else 0,
                    )

                # ------- pressed and released key ------
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.crosshair.kill()
                        pygame.mouse.set_visible(True)
                        return
                    if event.key == pygame.K_v:
                        target = self.predicted_crosshair.pos

                        move = target - self.start
                        move.normalize_ip()
                        move *= 200
                        a = move.angle_to(pygame.math.Vector2(1, 0))
                        rocket = SmarterRocket(
                            pos=pygame.math.Vector2(100, 400),
                            move=move,
                            angle=-a,
                            kill_on_edge=True,
                            color=(0, 0, 0),
                            moving_target_pos=(self.target1.pos.x, self.target1.pos.y),
                            target=(target.x, target.y),
                            direction=1 if self.target1.move.y > 0 else 0,
                        )

            # ------------ pressed keys ------
            pressed_keys = pygame.key.get_pressed()
            # ///

            # ---------- clear all --------------
            pygame.display.set_caption("Rocket Simulator | Moving-Target")
            pygame.display.set_icon(self.icon)
            self.screen.blit(self.background, (0, 0))

            # ----- draw cannon ------
            pygame.draw.circle(
                self.screen, (0, 200, 0), (int(self.start.x), int(self.start.y)), 5
            )

            # ----------- writing on screen ----------
            write(
                self.screen,
                "FPS: {:6.3}".format(self.clock.get_fps()),
                50,
                50,
                (0, 0, 250),
                20,
            )

            pygame.draw.line(
                self.background, (0, 0, 255), (800, 0), (800, Viewer.height)
            )

            # --------- update all sprites ----------------
            self.allgroup.update(seconds)
            self.predicted_crosshair.update(seconds, self.movingAgent, self.target1.pos, 1 if self.target1.move.y > 0 else 0, pspeed=(0,200))
            # --------- collision detection ------------
            for target in self.targetgroup:
                crashgroup = pygame.sprite.spritecollide(
                    target, self.beamgroup, False, pygame.sprite.collide_mask
                )
                for beam in crashgroup:
                    Explosion(pos=pygame.math.Vector2(beam.pos.x, beam.pos.y))
                    beam.kill(winner=True, writeData=False)

            # ---------- blit all sprites --------------
            self.allgroup.draw(self.screen)
            pygame.display.flip()

        pygame.mouse.set_visible(True)
        pygame.quit()
        # try:
        #    sys.exit()
        # finally:
        #    pygame.quit()


## -------------------- functions --------------------------------


def between(value, lower_limit=0, upper_limit=255):
    """makes sure a (color) value stays between a lower and a upper limit ( 0 and 255 )
    :param float value: the value that should stay between min and max
    :param float lower_limit:  the minimum value (lower limit)
    :param float upper_limit:  the maximum value (upper limit)
    :return: new_value"""
    return (
        lower_limit
        if value < lower_limit
        else upper_limit
        if value > upper_limit
        else value
    )


def cmp(a, b):
    """compares a with b, returns 1 if a > b, returns 0 if a==b and returns -1 if a < b"""
    return (a > b) - (a < b)


def randomize_colors(color, by=30):
    """randomize each color of a r,g,b tuple by the amount of +- by
    while staying between 0 and 255
    returns a color tuple"""
    r, g, b = color
    r += random.randint(-by, by)
    g += random.randint(-by, by)
    b += random.randint(-by, by)
    r = between(r)  # 0<-->255
    g = between(g)
    b = between(b)
    return r, g, b


def write(
    background,
    text,
    x=50,
    y=150,
    color=(0, 0, 0),
    font_size=None,
    font_name="mono",
    bold=True,
    origin="topleft",
):
    """blit text on a given pygame surface (given as 'background')
    the origin is the alignment of the text surface
    origin can be 'center', 'centercenter', 'topleft', 'topcenter', 'topright', 'centerleft', 'centerright',
    'bottomleft', 'bottomcenter', 'bottomright'
    """
    if font_size is None:
        font_size = 24
    font = pygame.font.SysFont(font_name, font_size, bold)
    width, height = font.size(text)
    surface = font.render(text, True, color)

    if origin == "center" or origin == "centercenter":
        background.blit(surface, (x - width // 2, y - height // 2))
    elif origin == "topleft":
        background.blit(surface, (x, y))
    elif origin == "topcenter":
        background.blit(surface, (x - width // 2, y))
    elif origin == "topright":
        background.blit(surface, (x - width, y))
    elif origin == "centerleft":
        background.blit(surface, (x, y - height // 2))
    elif origin == "centerright":
        background.blit(surface, (x - width, y - height // 2))
    elif origin == "bottomleft":
        background.blit(surface, (x, y - height))
    elif origin == "bottomcenter":
        background.blit(surface, (x - width // 2, y))
    elif origin == "bottomright":
        background.blit(surface, (x - width, y - height))


if __name__ == "__main__":
    # g = Game()
    Viewer(
        width=1200,
        height=800,
    )
