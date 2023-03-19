import math
import os
import pygame
from pygame import Color
from math import sin, radians, degrees, copysign
from pygame.math import Vector2
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
car_img_scale = .22
ppu = 20 * car_img_scale  # pixels per unit (foot in this case)


SCENARIO = "highland"

if SCENARIO == "dpw":
    image_scale = .90
    background_image = pygame.image.load(os.path.join(current_dir, 'dpw.png'))
    start_xy = (100, 60)
    start_angle = 140
elif SCENARIO == 'cong':
    background_image = pygame.image.load(os.path.join(current_dir, 'cong_church.png'))
    image_scale = .50
    start_xy = (30, 160)
    start_angle = 10
elif SCENARIO == 'highland':
    background_image = pygame.image.load(os.path.join(current_dir, 'highland.png'))
    image_scale = .50
    start_xy = (30, 50)
    start_angle = 270
elif SCENARIO == 'station':
    background_image = pygame.image.load(os.path.join(current_dir, 'station.png'))
    image_scale = .50
    start_xy = (170, 170)
    start_angle = 100

x, y = background_image.get_size()
background_image = pygame.transform.scale(background_image, (x * image_scale, y * image_scale))


class Car:
    def __init__(self):
        self.position = Vector2(start_xy)
        self.velocity = Vector2(0.0, 0.0)
        self.angle = start_angle
        self.length = 19  # L9 is 19 feet long
        self.track = 8  # 8' track
        self.max_steering = 45
        self.max_velocity = 20

        self.acceleration = 0.0
        self.steering = 0.0
        self.turning_radius = np.inf

        car_image_path = os.path.join(current_dir, "ladder.png")
        car_image = pygame.image.load(car_image_path)
        car_image = pygame.transform.scale(car_image, (655 * car_img_scale, 166 * car_img_scale))

        car_rect = car_image.get_rect()

        self.axle_offset = Vector2(-7, -.3)  # how far back the pivot points is from the center, in feet
        rear_to_front_vector = Vector2(self.length, 0)

        # draw a line on the axles
        rear_axle_point = np.asarray(car_rect.center) + (self.axle_offset * ppu)
        front_axle_point = rear_axle_point + rear_to_front_vector * ppu
        # pygame.draw.line(car_image, color=(0, 0, 0), start_pos=rear_axle_point, end_pos=front_axle_point)

        # draw the rear tires
        self.tire_width = .94  # for 12R22.5 tires on rear of L9
        tire_diameter = 3.58  # ditto
        tire_offset = 2
        self.track = 7.5
        # rear tires
        pygame.draw.rect(car_image, color=(0, 0, 0,), rect=pygame.Rect(
            rear_axle_point + ((tire_offset - .5 * tire_diameter) * ppu, self.track * .5 * ppu),
            (2.5 * ppu, self.tire_width * ppu)))
        pygame.draw.rect(car_image, color=(0, 0, 0,), rect=pygame.Rect(
            rear_axle_point + ((-tire_offset - .5 * tire_diameter) * ppu, self.track * .5 * ppu),
            (2.5 * ppu, self.tire_width * ppu)))
        pygame.draw.rect(car_image, color=(0, 0, 0,), rect=pygame.Rect(
            rear_axle_point + ((tire_offset - .5 * tire_diameter) * ppu, -self.track * .5 * ppu),
            (2.5 * ppu, self.tire_width * ppu)))
        pygame.draw.rect(car_image, color=(0, 0, 0,), rect=pygame.Rect(
            rear_axle_point + ((-tire_offset - .5 * tire_diameter) * ppu, -self.track * .5 * ppu),
            (2.5 * ppu, self.tire_width * ppu)))

        self.tire = pygame.Surface((2.5 * ppu, self.tire_width * ppu), pygame.SRCALPHA)
        pygame.draw.rect(self.tire, (0, 0, 0), pygame.Rect((0, 0), (2.5 * ppu, self.tire_width * ppu)))

        self.static_car_image = car_image
        self.car_image = self.static_car_image.copy()
        self.front_axle_point = front_axle_point

    def update(self, dt):
        if self.steering:
            self.turning_radius = self.length / sin(radians(self.steering))
            angular_velocity = self.velocity.x / self.turning_radius
        else:
            angular_velocity = 0

        self.position += self.velocity.rotate(-self.angle) * dt
        self.angle += degrees(angular_velocity) * dt

        # draw front tires
        self.car_image.blit(self.static_car_image, (0, 0))  # w/o front wheels
        rotated_tire = pygame.transform.rotate(self.tire, self.steering)
        rt_center = rotated_tire.get_rect().center
        self.car_image.blit(rotated_tire, self.front_axle_point - np.asarray(rt_center)/2 + (0, self.track * .5 * ppu))
        self.car_image.blit(rotated_tire, self.front_axle_point - np.asarray(rt_center)/2 + (0, -self.track * .5 * ppu))


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("L9 Turning Simulator")

        self.screen = pygame.display.set_mode(background_image.get_size())
        self.my_ft_font = pygame.freetype.SysFont(None, 20)
        self.clock = pygame.time.Clock()
        self.ticks = 60
        self.exit = False

        self.car = Car()  # makes a car object
        self.breadcrumbs = []

    def reset_game(self):
        self.car.velocity = Vector2(0, 0)
        self.car.position = Vector2(start_xy)
        self.car.steering = 0
        self.car.angle = start_angle
        self.breadcrumbs.clear()

    def run(self):
        car = self.car
        breadcrumbs = self.breadcrumbs
        show_guide = True
        last_breadcrumb_position = Vector2(0, 0)

        while not self.exit:
            dt = self.clock.get_time() / 1000

            # Event queue
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit = True

            # User input
            pressed = pygame.key.get_pressed()

            if pressed[pygame.K_UP]:
                car.velocity.x += .1
            elif pressed[pygame.K_DOWN]:
                car.velocity.x -= .1
            elif abs(car.velocity.x) < .1:
                car.velocity.x = 0
            car.velocity.x = max(-car.max_velocity, min(car.velocity.x, car.max_velocity))

            if pressed[pygame.K_RIGHT]:
                car.steering -= .5  # * dt
            elif pressed[pygame.K_LEFT]:
                car.steering += .5  # * dt
            elif pressed[pygame.K_SPACE]:
                car.velocity = Vector2(0, 0)
            car.steering = max(-car.max_steering, min(car.steering, car.max_steering))

            if pressed[pygame.K_c]:  # clear breadcrumbs
                breadcrumbs = []
            if pressed[pygame.K_g]:  # hide/show turning radius guide
                show_guide = not show_guide
            if pressed[pygame.K_r]:
                self.reset_game()

            # Logic
            car.update(dt)

            # Drawing
            self.screen.fill((255, 255, 255))  # make the background white

            # add the road image
            self.screen.blit(background_image, (0, 0))

            # draw the engine.  It needs to be placed such that the center of the rear axle is at the car location.
            # This makes it rotate about that position when turning.
            # The blit is placed relative to its upper left corner, so we need a transform
            # the rear axle center position depends on the angle
            rotated = pygame.transform.rotate(car.car_image, car.angle)
            rect = rotated.get_rect()  # gets the bounding box of the car rectangle after rotation
            img_center = np.array(rect.center)  # in screen space

            # transform the offset into screen space:
            delta_from_center = car.axle_offset.rotate(-car.angle)
            upper_left_corner = (car.position * ppu) - (img_center + np.asarray(delta_from_center) * ppu)
            self.screen.blit(rotated, upper_left_corner)

            # leave and show breadcrumbs
            bc_dist = (car.position - last_breadcrumb_position).length()
            if bc_dist > 1:
                breadcrumbs.append(car.position * ppu)
                last_breadcrumb_position = car.position.copy()
            for crumb in breadcrumbs:
                pygame.draw.circle(surface=self.screen, color=(0, 0, 0), center=crumb, radius=1, width=1)

            # add text
            dir_text = f'Steering: ' + (f'Left {abs(car.steering)}°' if car.steering > 0 else
                                        f'Right {abs(car.steering)}°' if car.steering < 0 else 'Centered')
            dir_text += f'    Speed: {car.velocity.x:.1f} mph'
            self.my_ft_font.render_to(self.screen, (100, 10), dir_text, (0, 0, 0))

            # draw turning radius arcs
            if car.steering != 0 and show_guide:
                turn_center = ((car.position.x - car.turning_radius * math.sin(radians(car.angle))) * ppu,
                               (car.position.y - car.turning_radius * math.cos(radians(car.angle))) * ppu
                               )
                # pygame.draw.line(self.screen, color=(0, 0, 0), start_pos=car.position * ppu, end_pos=turn_center)
                rad_ir = abs(car.turning_radius) - (car.track / 2)
                rad_or = abs(car.turning_radius) + (car.track / 2)
                rad_if = math.sqrt(rad_ir**2 + car.length**2)
                rad_of = math.sqrt(rad_or**2 + car.length**2)
                for r in [rad_ir, rad_or, rad_if, rad_of]:
                    pygame.draw.circle(surface=self.screen, color=Color(32, 32, 128), center=turn_center,
                                       radius=r * ppu, width=1)
                for r in [rad_if, rad_of]:
                    pygame.draw.circle(surface=self.screen, color=Color(32, 128, 32), center=turn_center,
                                       radius=r * ppu, width=1)

            pygame.display.flip()

            self.clock.tick(self.ticks)
        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.run()
