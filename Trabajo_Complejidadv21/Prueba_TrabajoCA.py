from flask import Flask, render_template, request
from flask_pymongo import PyMongo

import tkinter as tk
import heapq
import math
import threading

app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb+srv://teemo:u202214522@teemo.ck7qain.mongodb.net/TeemoDB"
mongo = PyMongo(app)

class Map:
    def __init__(self, master, map_image_file):
        self.master = master
        self.master.title("Ruta óptima")
        self.master.geometry("1000x600")
        self.map_image = tk.PhotoImage(file=map_image_file)

        self.canvas = tk.Canvas(self.master, width=1000, height=600)
        self.canvas.pack()

        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.map_image)

        self.ports = {
            'Europa': {},
            'Africa': {},
            'América': {},
            'Asia': {}
        }
        self.edges = {}
        self.trajectory = []

    def add_puerto(self, port, coordinates, continent):
        x = (coordinates[1] + 180) * (1200 / 360)
        y = (90 - coordinates[0]) * (800 / 180)
        self.ports[continent][port] = (x, y)
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
        for continent in self.ports:
            if port1 in self.ports[continent]:
                lat1, lon1 = self.ports[continent][port1]
            if port2 in self.ports[continent]:
                lat2, lon2 = self.ports[continent][port2]
        
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

     # Puertos peligrosos
     puertos_peligrosos_amarillo = {'Dubai', 'Shanghai'}
     puertos_peligrosos_rojo = {'Alexandria', 'Tokyo'}

     for i in range(len(route) - 1):
        for continent in self.ports:
            if route[i] in self.ports[continent]:
                x1, y1 = self.ports[continent][route[i]]
            if route[i + 1] in self.ports[continent]:
                x2, y2 = self.ports[continent][route[i + 1]]

        distance, curvature, direction = self.edges[route[i]][route[i + 1]]

        # Determina el color de la línea
        if route[i] in puertos_peligrosos_rojo or route[i + 1] in puertos_peligrosos_rojo:
            color = "red"
        elif route[i] in puertos_peligrosos_amarillo or route[i + 1] in puertos_peligrosos_amarillo:
            color = "yellow"
        else:
            color = "green"

        spline_curve = self.create_bezier_curve(x1, y1, x2, y2, curvature=curvature, direction=direction, color=color, visible=False)
        spline_points = self.interpolate_spline(spline_curve)
        spline_trajectory.extend(spline_points)

     self.boat = self.canvas.create_rectangle(spline_trajectory[0][0] - 10, spline_trajectory[0][1] - 10,
                                             spline_trajectory[0][0] + 50, spline_trajectory[0][1] + 50,
                                             fill="red")

     for i in range(1, len(spline_trajectory)):
        (x1, y1) = spline_trajectory[i - 1]
        (x2, y2) = spline_trajectory[i]
        # Aquí usamos la variable color determinada anteriormente
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2.4)
        self.canvas.coords(self.boat, x2 - 10, y2 - 10, x2 + 10, y2 + 10)
        self.master.update()
        self.master.after(4)



    def generate_html(self, route):
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Ruta óptima</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                }}
                .container {{
                    margin: 0 auto;
                    padding: 20px;
                    max-width: 800px;
                    text-align: center;
                }}
                .route {{
                    margin: 20px 0;
                }}
                .port {{
                    font-size: 18px;
                    color: blue;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Ruta óptima</h1>
                <div class="route">
                    <h2>Ruta encontrada:</h2>
                    {self.format_route(route)}
                </div>
            </div>
        </body>
        </html>
        """

        with open("templates/ruta_optima.html", "w", encoding="utf-8") as file:
            file.write(html_content)

    def format_route(self, route):
        formatted_route = ""
        for port in route:
            formatted_route += f'<div class="port">{port}</div><div>→</div>'
        formatted_route = formatted_route[:-14]  # Remove the last arrow
        return formatted_route

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/found')
def index():
    return render_template('Ruta optima.html')

@app.route('/find_route', methods=['POST'])
def find_route():
    start_port = request.form['start_port']
    end_port = request.form['end_port']
    
    def run_tkinter():
        root = tk.Tk()

        # Determina qué mapa usar según si hay puertos de Asia involucrados
        asia_ports = {'Tokyo', 'Shanghai', 'Singapore', 'Mumbai', 'Dubai' , 'Alexandria'}
        if start_port in asia_ports or end_port in asia_ports:
            map_file = 'static/mapa3.png'
        else:
            map_file = 'static/mapa2.png'

        map_widget = Map(root, map_file)

        if map_file == 'static/mapa3.png':

            # Elimina puertos y aristas de Europa, África y América que no son necesarios
            for port in list(map_widget.ports['Europa'].keys()):
                map_widget.deshabilitar_arista(port, port)
            for port in list(map_widget.ports['Africa'].keys()):
                map_widget.deshabilitar_arista(port, port)
            for port in list(map_widget.ports['América'].keys()):
                map_widget.deshabilitar_arista(port, port)

         # Puertos de Asia - America (con truquito)
            map_widget.add_puerto('Tokyo', (45.6895, -58.6917), 'Asia')
            map_widget.add_puerto('Shanghai', (40.2304, -80.4737), 'Asia')
            map_widget.add_puerto('Singapore', (5.3521, -95.8198), 'Asia')
            map_widget.add_puerto('Mumbai', (23.0760, -128.8777), 'Asia')
            map_widget.add_puerto('Dubai', (32.276987, -150.296249), 'Asia')
            map_widget.add_puerto('callao', (-2.276987, 55.296249), 'Asia')
            map_widget.add_puerto('Valparaiso', (-15.276987, 64), 'Asia')
            map_widget.add_puerto('Alexandria', (38.276987, -177.296249), 'Asia')
            # Aristas de Asia - America (con truquito)

            map_widget.add_arista('Tokyo', 'Shanghai', 1000, curvature=0.3, direction="in")
            map_widget.add_arista('Shanghai', 'Singapore', 1800, curvature=0.4, direction="out")
            map_widget.add_arista('Singapore', 'Mumbai', 3000, curvature=0.3, direction="out")
            map_widget.add_arista('Mumbai', 'Dubai', 1200, curvature=0.2, direction="in")
            map_widget.add_arista('Alexandria', 'Dubai', 500, curvature=0.2, direction="out")
            map_widget.add_arista('callao', 'Tokyo', 5000, curvature=0.2, direction="in")

        # ------------------Puertos------------------------
        else:
         #America
         map_widget.add_puerto('New York', (55.7128, -106.0060), 'América')
         map_widget.add_puerto('Los Angeles', (53.0522, -169.2437), 'América')
         map_widget.add_puerto('Panama City', (20.9824, -109.5199), 'América')
         map_widget.add_puerto('Manzanillo', (36.9824, -149.5199), 'América')
         map_widget.add_puerto('Buenos Aires', (-40.6037, -85.3816), 'América')
         map_widget.add_puerto('Rio de Janeiro', (-10.9068, -45.1729), 'América')
         map_widget.add_puerto('Guayana Francesa', (16.9068, -65.1729), 'América')
         map_widget.add_puerto('Callao', (0.9068, -106.1729), 'América')
         map_widget.add_puerto('Guayaquil', (8.5068, -110.1729), 'América')
         map_widget.add_puerto('Cartagena', (25.9068, -100.1729), 'América')
         map_widget.add_puerto('San Antonio', (-28.5068, -95.1729), 'América')
         map_widget.add_puerto('Montreal', (70.0, -100.0), 'América')
        
         # Europa
         map_widget.add_puerto('Portugal', (63.0, 2.5), 'Europa')
         map_widget.add_puerto('Valencia', (61.0, 15.5), 'Europa')
         map_widget.add_puerto('Hamburg', (83.6, 34.0), 'Europa')
         map_widget.add_puerto('Roterdam', (81.6, 24.0), 'Europa')
         map_widget.add_puerto('Le Havre', (70.5, 15.1), 'Europa')
         map_widget.add_puerto('Genova', (69.0, 30.5), 'Europa')
         map_widget.add_puerto('Atenas', (60.0, 49.5), 'Europa')
         map_widget.add_puerto('Casablanca', (52.0, 2.5), 'Europa')

         # África                           #arriba - lados
         map_widget.add_puerto('Nuakchot', (35.0, -7.5), 'Africa')
         map_widget.add_puerto('Dakar', (30.0, -10.5), 'Africa')
         map_widget.add_puerto('Abiyan', (19.0, 6.5), 'Africa')
         map_widget.add_puerto('Lagos', (19.0, 23.5), 'Africa')
         map_widget.add_puerto('Duban', (-33.0, 45.0), 'Africa')
         map_widget.add_puerto('Mombasa', (7.0, 80.0), 'Africa')
         map_widget.add_puerto('Toamasina', (-10.0, 93.0), 'Africa')
         map_widget.add_puerto('Port-Gentil', (10.0, 31.0), 'Africa')

         # ----------------Aristas----------------------

         #America
         map_widget.add_arista('New York', 'Portugal', 10000, curvature=0.3, direction="in")
         map_widget.add_arista('New York', 'Panama City', 1000, curvature=0.4, direction="in")
         map_widget.add_arista('Manzanillo', 'Panama City', 500, curvature=0.3, direction="in")
         map_widget.add_arista('Guayana Francesa', 'Cartagena', 200, curvature=0.5, direction="in")
         map_widget.add_arista('Cartagena', 'Panama City', 150, curvature=0.5, direction="in")
         map_widget.add_arista('Los Angeles', 'Panama City', 1200, curvature=0.3, direction="out")
         map_widget.add_arista('Callao', 'Guayaquil', 180, curvature=0.3, direction="out")
         map_widget.add_arista('Callao', 'San Antonio', 100, curvature=0.3, direction="out")
         map_widget.add_arista('Guayaquil', 'Panama City', 180, curvature=0.3, direction="out")
         map_widget.add_arista('Buenos Aires', 'Rio de Janeiro', 1000, curvature=0.3, direction="in")
         map_widget.add_arista('Rio de Janeiro', 'Guayana Francesa', 700, curvature=0.9, direction="in")
         map_widget.add_arista('Montreal', 'New York', 100, curvature=2, direction="in")
        
         # Europa
         map_widget.add_arista('Portugal', 'Le Havre', 110, curvature=0.6, direction="in")
         map_widget.add_arista('Portugal', 'Casablanca', 1000, curvature=0.2, direction="in")
         map_widget.add_arista('Roterdam', 'Le Havre', 100, curvature=0.5, direction="in")
         map_widget.add_arista('Roterdam', 'Hamburg', 20, curvature=0.5, direction="in")

         map_widget.add_arista('Genova', 'Valencia', 500, curvature=0.2, direction="out")
         map_widget.add_arista('Genova', 'Atenas', 600, curvature=0.5, direction="out")
         map_widget.add_arista('Casablanca', 'Valencia', 200, curvature=0.2, direction="out")


         # África
         map_widget.add_arista('Nuakchot', 'Casablanca', 200, curvature=0.5, direction="in")
         map_widget.add_arista('Nuakchot', 'Dakar', 50, curvature=0.5, direction="in")
         map_widget.add_arista('Dakar', 'Abiyan', 100, curvature=0.5, direction="in")
         map_widget.add_arista('Abiyan', 'Lagos', 180, curvature=0.6, direction="in")
         map_widget.add_arista('Lagos', 'Port-Gentil', 70, curvature=0.5, direction="in")
         map_widget.add_arista('Duban', 'Port-Gentil', 800, curvature=0.7, direction="in")
         map_widget.add_arista('Duban', 'Toamasina', 700, curvature=0.7, direction="out")
         map_widget.add_arista('Mombasa', 'Toamasina', 250, curvature=1.2, direction="out")

        pass

        route = map_widget.a_star(start_port, end_port)
        if route:
            print("Ruta encontrada:", route)
            map_widget.animate_route(route)
            map_widget.generate_html(route)
            return render_template('prueba.html', route=route)
        else:
            print("No se encontró una ruta")
            return render_template('prueba.html', route=None)
        
        root.mainloop()

    threading.Thread(target=run_tkinter).start()

    return render_template('prueba.html')

if __name__ == '__main__':
    app.run(debug=True)
