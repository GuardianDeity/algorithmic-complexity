import tkinter as tk
import heapq
import math

class Map:
    def __init__(self, master):
        self.master = master
        self.master.title("Ruta óptima")
        self.master.geometry("1000x600") 
        self.map_image = tk.PhotoImage(file="mapa.png")  

        self.canvas = tk.Canvas(self.master, width=1000, height=600)
        self.canvas.pack()

        
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.map_image)

        self.ports = {}
        self.edges = {}
        self.trajectory = []

    def add_puerto(self, port, coordinates):
        # Convertir coordenadas de latitud/longitud a escala de la ventana
        x = (coordinates[1] + 180) * (1200 / 360)
        y = (90 - coordinates[0]) * (800 / 180)
        self.ports[port] = (x, y)
        self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="blue")
        self.canvas.create_text(x, y-10, text=port, font=("Arial", 10, "bold"))

    def add_arista(self, port1, port2, distance):
        if port1 not in self.edges:
            self.edges[port1] = {}
        if port2 not in self.edges:
            self.edges[port2] = {}
        self.edges[port1][port2] = distance
        self.edges[port2][port1] = distance  # ruta bi direcional
        # Dibujar la arista
        x1, y1 = self.ports[port1]
        x2, y2 = self.ports[port2]
        self.canvas.create_line(x1, y1, x2, y2, fill="black")

    def dashabilitar_arista(self, port1, port2):
        if port1 in self.edges and port2 in self.edges[port1]:
            del self.edges[port1][port2]
            del self.edges[port2][port1]

    def a_star(self, start, goal):
        open_list = []
        closed_list = set()
        heapq.heappush(open_list, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}

        while open_list:
            current = heapq.heappop(open_list)[1]
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path

            closed_list.add(current)
            for neighbor in self.edges.get(current, {}):
                if neighbor in closed_list:
                    continue
                tentative_g_score = g_score[current] + self.edges[current][neighbor]
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor]= tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    heapq.heappush(open_list, (f_score[neighbor], neighbor))

        return None

    def heuristic(self, port1, port2):
        lat1, lon1 = self.ports[port1]
        lat2, lon2 = self.ports[port2]
        R = 6371  # radio de la Tierra en km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c

        return distance

    def animate_route(self, route):
        self.trajectory = [(self.ports[port][0], self.ports[port][1]) for port in route]
        self.canvas.create_line(*self.trajectory, fill="red", width=2)

        self.boat = self.canvas.create_rectangle(self.ports[route[0]][0]-10, self.ports[route[0]][1]-10, self.ports[route[0]][0]+10, self.ports[route[0]][1]+10, fill="red")

        for i in range(len(route)-1):
            x1, y1 = self.ports[route[i]]
            x2, y2 = self.ports[route[i+1]]

            
            dx = x2 - x1
            dy = y2 - y1
            steps = int(max(abs(dx), abs(dy)) // 2)  

            for j in range(steps):
                x_interp = x1 + (dx * j / steps)
                y_interp = y1 + (dy * j / steps)
                self.canvas.coords(self.boat, x_interp-10, y_interp-10, x_interp+10, y_interp+10)
                self.master.update()
                self.master.after(20)  # velocidad para barcola

root = tk.Tk()
map_widget = Map(root)

#puertos:
#europa
map_widget.add_puerto('Portugal', (63.0, 2.5))  
map_widget.add_puerto('Hamburg', (83.6, 30.0))   
map_widget.add_puerto('Le Havre', (70.5, 15.1))

#africa
map_widget.add_puerto('Nuakchot', (34.0,-8.0))  

#america
map_widget.add_puerto('New York', (55.7128, -106.0060))
map_widget.add_puerto('Los Angeles', (53.0522, -169.2437))
map_widget.add_puerto('Panama City', (20.9824, -109.5199))
map_widget.add_puerto('Buenos Aires', (-40.6037, -85.3816))
map_widget.add_puerto('Rio de Janeiro', (-10.9068, -45.1729))
map_widget.add_puerto('Guayana Francesa', (16.9068, -65.1729))
map_widget.add_puerto('Callao', (0.9068, -106.1729))

#aristas:
#europa
map_widget.add_arista('Portugal', 'Hamburg', 350)
map_widget.add_arista('Portugal', 'Le Havre', 200)
map_widget.add_arista('Hamburg', 'Le Havre', 450)
map_widget.add_arista('Nuakchot', 'Portugal',300)
#america - europa
map_widget.add_arista('Portugal', 'New York', 6000)
map_widget.add_arista('New York', 'Panama City', 3500)
map_widget.add_arista('Panama City', 'Los Angeles', 4800)
map_widget.add_arista('Buenos Aires', 'Rio de Janeiro', 2000)
map_widget.add_arista('Panama City', 'Guayana Francesa', 1000)
map_widget.add_arista('Guayana Francesa', 'Rio de Janeiro', 500)

map_widget.add_arista('Callao', 'Panama City', 700)


# Calcular la ruta óptima y animarla
route = map_widget.a_star('Portugal', 'Buenos Aires')
map_widget.animate_route(route)

root.mainloop()
