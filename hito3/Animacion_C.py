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
        x = (coordinates[1] + 180) * (1200 / 360)
        y = (90 - coordinates[0]) * (800 / 180)
        self.ports[port] = (x, y)
        self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="blue")
        self.canvas.create_text(x, y-10, text=port, font=("Arial", 8, "bold"))

    def add_arista(self, port1, port2, distance, curvature=0.3, direction="out"):
        if (port1, port2) in self.edges or (port2, port1) in self.edges:
            return

        if port1 not in self.edges:
            self.edges[port1] = {}
        if port2 not in self.edges:
            self.edges[port2] = {}

        self.edges[port1][port2] = (distance, curvature, direction)
        self.edges[port2][port1] = (distance, curvature, direction)

    def deshabilitar_arista(self, port1, port2):
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
                tentative_g_score = g_score[current] + self.edges[current][neighbor][0]
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    heapq.heappush(open_list, (f_score[neighbor], neighbor))

        return None

    def heuristic(self, port1, port2):
        lat1, lon1 = self.ports[port1]
        lat2, lon2 = self.ports[port2]
        R = 6371

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c

        return distance

    def create_bezier_curve(self, x1, y1, x2, y2, curvature=0.3, direction="out", color="black", width=1, visible=True):
        if direction == "out":
            cx = (x1 + x2) / 2 + curvature * (y2 - y1)
            cy = (y1 + y2) / 2 - curvature * (x2 - x1)
        else:  # "in"
            cx = (x1 + x2) / 2 - curvature * (y2 - y1)
            cy = (y1 + y2) / 2 + curvature * (x2 - x1)
        
        points = [x1, y1, cx, cy, x2, y2]
        if visible:
            self.canvas.create_line(points, fill=color, smooth=True, splinesteps=60, width=width)
        return points

    def interpolate_spline(self, points, num_steps=100):
        spline_coords = []
        for i in range(num_steps + 1):
            t = i / num_steps
            x = (1 - t)**2 * points[0] + 2 * (1 - t) * t * points[2] + t**2 * points[4]
            y = (1 - t)**2 * points[1] + 2 * (1 - t) * t * points[3] + t**2 * points[5]
            spline_coords.append((x, y))
        return spline_coords

    def animate_route(self, route):
        spline_trajectory = []

        for i in range(len(route) - 1):
            x1, y1 = self.ports[route[i]]
            x2, y2 = self.ports[route[i + 1]]
            distance, curvature, direction = self.edges[route[i]][route[i + 1]]
            spline_curve = self.create_bezier_curve(x1, y1, x2, y2, curvature=curvature, direction=direction, color="blue", visible=False)
            spline_points = self.interpolate_spline(spline_curve)
            spline_trajectory.extend(spline_points)

        self.boat = self.canvas.create_rectangle(spline_trajectory[0][0] - 10, spline_trajectory[0][1] - 10,
                                                 spline_trajectory[0][0] + 50, spline_trajectory[0][1] + 50,
                                                 fill="red")

        for i in range(1, len(spline_trajectory)):
            (x1, y1) = spline_trajectory[i - 1]
            (x2, y2) = spline_trajectory[i]
            self.canvas.create_line(x1, y1, x2, y2, fill="red", width=2.4)
            self.canvas.coords(self.boat, x2 - 10, y2 - 10, x2 + 10, y2 + 10)
            self.master.update()
            self.master.after(4)

root = tk.Tk()
map_widget = Map(root)

# Puertos
# Europa
map_widget.add_puerto('Portugal', (63.0, 2.5))
map_widget.add_puerto('Hamburg', (83.6, 30.0))
map_widget.add_puerto('Le Havre', (70.5, 15.1))
map_widget.add_puerto('Genova', (70.0, 30.0))
# África
map_widget.add_puerto('Nuakchot', (34.0, -8.0))
map_widget.add_puerto('Casablanca', (53.0, 5.0))
map_widget.add_puerto('Duban', (-28.0, 45.0))
map_widget.add_puerto('Accra', (19.0, 15.0))
# América
map_widget.add_puerto('New York', (55.7128, -106.0060))
map_widget.add_puerto('Los Angeles', (53.0522, -169.2437))
map_widget.add_puerto('Panama City', (20.9824, -109.5199))
map_widget.add_puerto('Buenos Aires', (-40.6037, -85.3816))
map_widget.add_puerto('Rio de Janeiro', (-10.9068, -45.1729))
map_widget.add_puerto('Guayana Francesa', (16.9068, -65.1729))
map_widget.add_puerto('Callao', (0.9068, -106.1729))
map_widget.add_puerto('Montreal', (70.0, -100.0))

# Aristas
# Europa
map_widget.add_arista('Portugal', 'Hamburg', 600, curvature=0.3, direction="in")
map_widget.add_arista('Portugal', 'Le Havre', 110, curvature=0.6, direction="in")
map_widget.add_arista('Portugal', 'Casablanca', 1000, curvature=0.2, direction="out")
map_widget.add_arista('Le Havre', 'Hamburg', 100, curvature=0.5, direction="in")
map_widget.add_arista('Genova', 'Casablanca', 1000, curvature=0.2, direction="out")


# África
map_widget.add_arista('Nuakchot', 'Casablanca', 200, curvature=0.5, direction="out")
map_widget.add_arista('Nuakchot', 'Accra', 150, curvature=1.5, direction="out")
map_widget.add_arista('Accra', 'Duban', 180, curvature=0.5, direction="out")
map_widget.add_arista('Nuakchot', 'Duban', 1000, curvature=0.5, direction="out")


# América
map_widget.add_arista('New York', 'Portugal', 10000, curvature=0.3, direction="in")
map_widget.add_arista('New York', 'Panama City', 1000, curvature=0.4, direction="out")
map_widget.add_arista('Guayana Francesa', 'Panama City', 200, curvature=0.5, direction="out")
map_widget.add_arista('Los Angeles', 'Panama City', 1200, curvature=0.3, direction="out")
map_widget.add_arista('Panama City', 'Callao', 180, curvature=0.3, direction="in")
map_widget.add_arista('Buenos Aires', 'Rio de Janeiro', 1000, curvature=0.3, direction="out")
map_widget.add_arista('Rio de Janeiro', 'Guayana Francesa', 700, curvature=0.9, direction="out")
map_widget.add_arista('Montreal', 'New York', 100, curvature=2, direction="in")

# Ejemplo de uso
def find_route():
    start_port = "Duban"
    end_port = "Buenos Aires"

    # Deshabilitar una ruta específica
    #map_widget.deshabilitar_arista("Duban", "Accra")
    #print(f"Ruta desde {start_port} hasta {end_port}")

    route = map_widget.a_star(start_port, end_port)
    if route:
        print("Ruta encontrada:", route)
        map_widget.animate_route(route)
    else:
        print("No se encontró una ruta")

find_route()

root.mainloop()


