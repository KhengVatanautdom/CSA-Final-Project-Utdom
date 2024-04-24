import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 800))
pygame.display.set_caption("Button!")
main_font = pygame.font.SysFont("cambria", 50)

class Login():
	def __init__(self, image, x_pos, y_pos, text_input):
		self.image = image
		self.x_pos = x_pos
		self.y_pos = y_pos
		self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
		self.text_input = text_input
		self.text = main_font.render(self.text_input, True, "white")
		self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))

	def update(self):
		screen.blit(self.image, self.rect)
		screen.blit(self.text, self.text_rect)

	def checkForInput(self, position):
		if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
			print("Button Press!")

	def changeColor(self, position):
		if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
			self.text = main_font.render(self.text_input, True, "green")
		else:
			self.text = main_font.render(self.text_input, True, "white")




class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = (0, 0, 0)
        self.text = text
        self.txt_surface = main_font.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = (0, 255, 0) if self.active else (0, 0, 0)
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    # Handle user pressing Enter (log in action)
                    print("User name:", self.text)
                    # Transition to the main menu or the actual game
                    # (replace this with your actual logic)
                    self.text = ''  # Clear the input box after logging in
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                self.txt_surface = main_font.render(self.text, True, self.color)

    def render(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, 2)
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))


button_surface = pygame.image.load("button.png")
button_surface = pygame.transform.scale(button_surface, (400, 150))

button = Login(button_surface, 400, 400, "Log in")
input_box = InputBox(400, 200, 200, 50)
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            button.checkForInput(pygame.mouse.get_pos())
            input_box.handle_event(event)  # Handle input box events

    screen.fill("white")

    button.update()
    button.changeColor(pygame.mouse.get_pos())

    # Render the input box
    pygame.draw.rect(screen, input_box.color, input_box.rect, 2)
    screen.blit(input_box.txt_surface, (input_box.rect.x + 5, input_box.rect.y + 5))

    pygame.display.update()