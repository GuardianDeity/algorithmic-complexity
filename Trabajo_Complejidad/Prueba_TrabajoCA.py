from flask import Flask, render_template, request
import tkinter as tk
import heapq
import math
import threading

app = Flask(__name__)

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
        self.canvas.create_oval(x-4, y-4, x+4, y+4, fill="blue")
        self.canvas.create_text(x, y-10, text=port, font=("Arial", 7, "bold"))

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
     lat1, lon1 = None, None
     lat2, lon2 = None, None

     for continent in self.ports:
        if port1 in self.ports[continent]:
            lat1, lon1 = self.ports[continent][port1]
        if port2 in self.ports[continent]:
            lat2, lon2 = self.ports[continent][port2]

     if lat1 is None or lat2 is None or lon1 is None or lon2 is None:
        raise ValueError(f"Coordenadas no encontradas para los puertos: {port1}, {port2}")

     dlat = math.radians(lat2 - lat1)
     dlon = math.radians(lon2 - lon1)
     a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
     distance = 6371 * c 

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
     puertos_peligrosos_rojo = {'Alexandria', 'toamasina','Toamasina','alexandria','eupatoria','Eupatoria'}

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
def index():
    return render_template('Ruta optima.html')

@app.route('/find_route', methods=['POST'])
def find_route():
    start_port = request.form['start_port']
    end_port = request.form['end_port']
    
    def run_tkinter():
        root = tk.Tk()

        # Determina qué mapa usar según si hay puertos de Asia involucrados
        asia_ports = {'Tokyo', 'Shanghai', 'Singapore', 'Mumbai', 'Dubai', 'Alexandria','Tianjing','Hon Kong','Quanzhou',
                      'Zhanjiang','callao','Valparaiso','fort lauderdale','abiyan','durban','mombasa','toamasina'
                      ,'port-Gentil','Tuticorin','Sidney','Brisbane','Fremantle','Darwin','Moresby','Chennai',
                      'San Petersburgo','Copenhague','Arkits','Murmansk','genova','atenas','valencia','le havre',
                      'hamburg','Arkits','Uelen','Stavanger'}
        if start_port in asia_ports or end_port in asia_ports:
            map_file = 'mapa3.png'
        else:
            map_file = 'mapa2.png'

        map_widget = Map(root, map_file)

        if map_file == 'mapa3.png':

            # Elimina puertos y aristas de Europa, África y América que no son necesarios
            for port in list(map_widget.ports['Europa'].keys()):
                map_widget.deshabilitar_arista(port, port)
            for port in list(map_widget.ports['Africa'].keys()):
                map_widget.deshabilitar_arista(port, port)
            for port in list(map_widget.ports['América'].keys()):
                map_widget.deshabilitar_arista(port, port)

         # Puertos de Asia - America (con truquito)
            map_widget.add_puerto('Tokyo', (31.6895, -34.6917), 'Asia')
            map_widget.add_puerto('Busan', (30.6895, -43.6917), 'Asia')
            map_widget.add_puerto('Shanghai', (27.2304, -50.4737), 'Asia')
            map_widget.add_puerto('Tianjing', (34.2304, -55.4737), 'Asia')
            map_widget.add_puerto('Hon Kong', (19.2304, -58.4737), 'Asia')
            map_widget.add_puerto('Quanzhou', (22.2304, -51.4737), 'Asia')
            map_widget.add_puerto('Zhanjiang', (35.2304, -45.4737), 'Asia')
            
            map_widget.add_puerto('Singapore', (5.3521, -65.8198), 'Asia')
            map_widget.add_puerto('Yakarta', (0, -64), 'Asia')
            map_widget.add_puerto('Mumbai', (18.0760, -98.8777), 'Asia')
            map_widget.add_puerto('Chennai', (14, -89.8198), 'Asia')
            map_widget.add_puerto('Tuticorin', (9, -92.8198), 'Asia')
            map_widget.add_puerto('Dubai', (22.276987, -118.296249), 'Asia')
            map_widget.add_puerto('Alexandria', (26.276987, -142.296249), 'Asia')
            map_widget.add_puerto('Aden', (13, -128), 'Asia')
            map_widget.add_puerto('San Petersburgo', (52, -147), 'Asia')
            map_widget.add_puerto('Murmansk', (62, -147), 'Asia')
            map_widget.add_puerto('Arkits', (75, -128), 'Asia')
            map_widget.add_puerto('Uelen', (77, -16), 'Asia')
            map_widget.add_puerto('Copenhague', (47, -163), 'Asia')
            map_widget.add_puerto('Mascate', (17, -115.296249), 'Asia')


            map_widget.add_puerto('Sidney', (-23, -21), 'Asia')
            map_widget.add_puerto('Brisbane', (-19, -17), 'Asia')
            map_widget.add_puerto('Fremantle', (-20, -57), 'Asia')
            map_widget.add_puerto('Darwin', (-5, -35), 'Asia')
            map_widget.add_puerto('Moresby', (-3, -21), 'Asia')

            #america - asia
            map_widget.add_puerto('callao', (-11.276987, 65.296249), 'Asia')
            map_widget.add_puerto('buenos aires', (-34.276987, 89), 'Asia')
            map_widget.add_puerto('Valparaiso', (-27.276987, 75), 'Asia')
            map_widget.add_puerto('Rio de janeiro', (-20.9068, 110.1729), 'Asia')
            map_widget.add_puerto('fort lauderdale', (18.276987, 64), 'Asia')
            map_widget.add_puerto('guayaquil', (-4.276987, 62.5), 'Asia')
            map_widget.add_puerto('balboa', (3.276987, 64), 'Asia')
            map_widget.add_puerto('manzanilla', (14, 34), 'Asia')
            map_widget.add_puerto('long beach', (25, 22), 'Asia')
            map_widget.add_puerto('new york', (31, 74), 'Asia')
            map_widget.add_puerto('houston', (21, 50), 'Asia')
            map_widget.add_puerto('san francisco', (29, 19), 'Asia')
            map_widget.add_puerto('vancouver', (42, 23), 'Asia')
            map_widget.add_puerto('prince roupert', (49, 20), 'Asia')
            map_widget.add_puerto('Guayana francesa', (0, 96), 'Asia')
            map_widget.add_puerto('cartagena', (6, 70), 'Asia')
            map_widget.add_puerto('cabello', (5, 80), 'Asia')


            #africa - asia
            map_widget.add_puerto('abiyan', (8.0, -177.5), 'Africa')
            map_widget.add_puerto('durban', (-20.0, -150.0), 'Africa')
            map_widget.add_puerto('mombasa', (2.5, -133.0), 'Africa')
            map_widget.add_puerto('toamasina', (-8.0, -124.0), 'Africa')
            map_widget.add_puerto('port-Gentil', (4.0, -165.0), 'Africa')

            #europa - asia
            map_widget.add_puerto('genova', (35.276987, -165.296249), 'Asia')
            map_widget.add_puerto('atenas', (31.276987, -152.296249), 'Asia')
            map_widget.add_puerto('valencia', (32.276987, -174.296249), 'Asia')
            map_widget.add_puerto('le havre', (37.276987, -174.296249), 'Asia')
            map_widget.add_puerto('hamburg', (43.276987, -167.296249), 'Asia')
            map_widget.add_puerto('eupatoria', (37.276987, -140.296249), 'Asia')
            map_widget.add_puerto('Stavanger', (52.276987, -168.296249), 'Asia')

            # Aristas de Asia - America (con truquito)

            map_widget.add_arista('Tokyo', 'Busan', 200, curvature=0.3, direction="in")
            map_widget.add_arista('Shanghai', 'Busan', 150, curvature=0.3, direction="in")
            map_widget.add_arista('Shanghai', 'Quanzhou', 200, curvature=0.3, direction="out")
            map_widget.add_arista('Hon Kong', 'Quanzhou', 100, curvature=0.4, direction="out")
            map_widget.add_arista('Hon Kong', 'Singapore', 100, curvature=0.3, direction="out")
            map_widget.add_arista('Singapore', 'Chennai', 300, curvature=0.2, direction="out")
            map_widget.add_arista('Singapore', 'Yakarta', 200, curvature=0.3, direction="out")
            map_widget.add_arista('Singapore', 'Tuticorin', 200, curvature=0.3, direction="in")
            map_widget.add_arista('Chennai', 'Tuticorin', 3000, curvature=0.3, direction="out")
            map_widget.add_arista('Mumbai', 'Tuticorin', 1200, curvature=0.2, direction="out")
            map_widget.add_arista('Mumbai', 'Mascate', 500, curvature=0.2, direction="out")
            map_widget.add_arista('Mumbai', 'Dubai', 400, curvature=0.3, direction="out")
            map_widget.add_arista('Aden', 'Mascate', 400, curvature=0.2, direction="out")
            map_widget.add_arista('Aden', 'Alexandria', 500, curvature=0.1, direction="out")
            map_widget.add_arista('Yakarta', 'Darwin', 2000, curvature=0.2, direction="in")
            map_widget.add_arista('Darwin', 'Fremantle', 500, curvature=0.2, direction="in")
            map_widget.add_arista('Darwin', 'Brisbane', 500, curvature=0.7, direction="out")       
            map_widget.add_arista('Darwin', 'Moresby', 300, curvature=0.2, direction="out") 
            map_widget.add_arista('Moresby', 'Brisbane', 2000, curvature=0.2, direction="in")
            map_widget.add_arista('Brisbane', 'Sidney', 200, curvature=0.2, direction="out")

            #america
            map_widget.add_arista('san francisco', 'Tokyo', 5000, curvature=0.2, direction="in")
            map_widget.add_arista('Rio de janeiro', 'buenos aires', 200, curvature=0.2, direction="in")
            map_widget.add_arista('Rio de janeiro', 'Guayana francesa', 200, curvature=1.0, direction="in")
            map_widget.add_arista('cabello', 'Guayana francesa', 200, curvature=0.2, direction="in")
            map_widget.add_arista('cabello', 'cartagena', 200, curvature=0.2, direction="in")
            map_widget.add_arista('cartagena', 'balboa', 200, curvature=0.2, direction="in")
            map_widget.add_arista('callao', 'Valparaiso', 150, curvature=0.2, direction="in")
            map_widget.add_arista('callao', 'guayaquil', 200, curvature=0.2, direction="out")
            map_widget.add_arista('guayaquil', 'balboa', 250, curvature=0.2, direction="out")
            map_widget.add_arista('balboa', 'manzanilla', 500, curvature=0.2, direction="out")
            map_widget.add_arista('manzanilla', 'long beach', 200, curvature=0.2, direction="out")
            map_widget.add_arista('long beach', 'san francisco', 100, curvature=0.2, direction="out")
            map_widget.add_arista('new york', 'fort lauderdale', 200, curvature=0.2, direction="out")
            map_widget.add_arista('balboa', 'fort lauderdale', 200, curvature=0.2, direction="in")
            map_widget.add_arista('houston', 'balboa', 200, curvature=0.2, direction="in")



            #africa
            map_widget.add_arista('toamasina', 'Tuticorin', 2000, curvature=0.2, direction="in")
            map_widget.add_arista('toamasina', 'mombasa', 200, curvature=0.2, direction="in")
            map_widget.add_arista('toamasina', 'durban', 2000, curvature=0.2, direction="in")
            map_widget.add_arista('port-Gentil', 'durban', 1000, curvature=0.2, direction="in")

            #europa - asia
            map_widget.add_arista('San Petersburgo', 'Copenhague', 200, curvature=0.1, direction="in")
            map_widget.add_arista('Copenhague', 'Murmansk', 800, curvature=2.3, direction="out")
            map_widget.add_arista('Murmansk', 'Arkits', 200, curvature=0.3, direction="out")
            map_widget.add_arista('Uelen', 'Arkits', 200, curvature=0.3, direction="out")
            map_widget.add_arista('Uelen', 'Tokyo', 200, curvature=0.3, direction="out")
            map_widget.add_arista('eupatoria', 'atenas', 200, curvature=0.3, direction="out")
            map_widget.add_arista('genova', 'atenas', 200, curvature=0.3, direction="out")
            map_widget.add_arista('genova', 'valencia', 200, curvature=0.3, direction="out")
            map_widget.add_arista('le havre', 'valencia', 200, curvature=3.3, direction="out")
            map_widget.add_arista('le havre', 'hamburg', 200, curvature=0.7, direction="out")
            map_widget.add_arista('Copenhague', 'hamburg', 200, curvature=0.3, direction="out")
            map_widget.add_arista('Copenhague', 'Stavanger', 200, curvature=0.7, direction="out")
            map_widget.add_arista('Stavanger', 'Murmansk', 200, curvature=0.6, direction="out")

        # ------------------Puertos------------------------
        else:
         #America
         map_widget.add_puerto('New York', (55.7128, -106.0060), 'América')
         map_widget.add_puerto('Long Beach', (54, -169.0060), 'América')
         map_widget.add_puerto('San Francisco', (59.7128, -173.0060), 'América')
         map_widget.add_puerto('Fort Lauderdale', (43.7128, -111.0060), 'América')
         map_widget.add_puerto('Panama City', (20.9824, -109.5199), 'América')
         map_widget.add_puerto('Manzanillo', (36.9824, -149.5199), 'América')
         map_widget.add_puerto('Buenos Aires', (-40.6037, -85.3816), 'América')
         map_widget.add_puerto('Rio de Janeiro', (-10.9068, -45.1729), 'América')
         map_widget.add_puerto('Rio Grande', (-30.9068, -70.1729), 'América')
         map_widget.add_puerto('Guayana Francesa', (16.9068, -65.1729), 'América')
         map_widget.add_puerto('Callao', (0.9068, -106.1729), 'América')
         map_widget.add_puerto('Guayaquil', (8.5068, -110.1729), 'América')
         map_widget.add_puerto('Cartagena', (25.9068, -100.1729), 'América')
         map_widget.add_puerto('Cabello', (23.9068, -85.1729), 'América')
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
         map_widget.add_puerto('Mersin', (58.0, 66.0), 'Africa')
         map_widget.add_puerto('Constanza', (70.0, 61.0), 'Africa')
         map_widget.add_puerto('Eupatoria', (68.0, 70.0), 'Africa')
         map_widget.add_puerto('Estambul', (64.0, 60.0), 'Africa')


         # África                           #arriba - lados
         map_widget.add_puerto('Nuakchot', (35.0, -7.5), 'Africa')
         map_widget.add_puerto('Dakar', (30.0, -10.5), 'Africa')
         map_widget.add_puerto('Abiyan', (19.0, 6.5), 'Africa')
         map_widget.add_puerto('Lagos', (19.0, 23.5), 'Africa')
         map_widget.add_puerto('Walbys bay', (-15.0, 40), 'Africa')
         map_widget.add_puerto('Durban', (-31.0, 48.0), 'Africa')
         map_widget.add_puerto('Mombasa', (7.0, 80.0), 'Africa')
         map_widget.add_puerto('Toamasina', (-10.0, 93.0), 'Africa')
         map_widget.add_puerto('Port-Gentil', (10.0, 31.0), 'Africa')
         map_widget.add_puerto('Luanda', (-1.0, 39.0), 'Africa')
         map_widget.add_puerto('alexandria', (51.0, 66.0), 'Africa')
         map_widget.add_puerto('aden', (28.0,85.0), 'Africa')
         map_widget.add_puerto('Mogadiscio', (20.0,95.0), 'Africa')



         #Asia
         map_widget.add_puerto('mascate', (35.0,108.0), 'Africa')
         map_widget.add_puerto('dubai', (43.0,105.0), 'Africa')

         # ----------------Aristas----------------------

         #America
         map_widget.add_arista('New York', 'Portugal', 10000, curvature=0.3, direction="in")
         map_widget.add_arista('Fort Lauderdale', 'Panama City', 700, curvature=0.4, direction="in")
         map_widget.add_arista('Fort Lauderdale', 'New York', 700, curvature=0.4, direction="in")
         map_widget.add_arista('Cartagena', 'Panama City', 100, curvature=0.4, direction="in")
         map_widget.add_arista('Cartagena', 'Fort Lauderdale', 200, curvature=0.4, direction="in")
         map_widget.add_arista('Manzanillo', 'Panama City', 500, curvature=0.3, direction="in")
         map_widget.add_arista('Cabello', 'Cartagena', 100, curvature=0.5, direction="in")
         map_widget.add_arista('Callao', 'Guayaquil', 180, curvature=0.3, direction="out")
         map_widget.add_arista('Callao', 'San Antonio', 100, curvature=0.3, direction="out")
         map_widget.add_arista('Guayaquil', 'Panama City', 180, curvature=0.3, direction="out")
         map_widget.add_arista('Guayana Francesa', 'Cabello', 100, curvature=0.3, direction="in")
         map_widget.add_arista('Guayana Francesa', 'Rio de Janeiro', 1000, curvature=0.3, direction="in")
         map_widget.add_arista('Rio Grande', 'Rio de Janeiro', 100, curvature=0.3, direction="in")
         map_widget.add_arista('Buenos Aires', 'Rio Grande', 100, curvature=0.3, direction="in")
         map_widget.add_arista('Rio de Janeiro', 'Guayana Francesa', 700, curvature=0.9, direction="in")
         map_widget.add_arista('Montreal', 'New York', 100, curvature=2, direction="in")
         map_widget.add_arista('Long Beach', 'San Francisco',100,curvature=0.3, direction="out")
         map_widget.add_arista('Long Beach', 'Manzanillo',100,curvature=0.3, direction="out")
        
         # Europa
         map_widget.add_arista('Portugal', 'Le Havre', 110, curvature=0.6, direction="in")
         map_widget.add_arista('Portugal', 'Casablanca', 1000, curvature=0.2, direction="in")
         map_widget.add_arista('Roterdam', 'Le Havre', 100, curvature=0.5, direction="in")
         map_widget.add_arista('Roterdam', 'Hamburg', 20, curvature=0.5, direction="in")

         map_widget.add_arista('Genova', 'Valencia', 500, curvature=0.2, direction="out")
         map_widget.add_arista('Genova', 'Atenas', 600, curvature=0.5, direction="in")
         map_widget.add_arista('Estambul', 'Atenas', 200, curvature=0.5, direction="in")
         map_widget.add_arista('Estambul', 'Constanza', 300, curvature=0.1, direction="in")
         map_widget.add_arista('Estambul', 'Eupatoria', 300, curvature=0.1, direction="in")
         map_widget.add_arista('Mersin', 'Atenas', 200, curvature=0.5, direction="out")
         map_widget.add_arista('Mersin', 'alexandria', 600, curvature=0.5, direction="out")
         map_widget.add_arista('Casablanca', 'Valencia', 100, curvature=0.2, direction="out")


         # África
         map_widget.add_arista('Nuakchot', 'Casablanca', 200, curvature=0.5, direction="in")
         map_widget.add_arista('Nuakchot', 'Dakar', 50, curvature=0.5, direction="in")
         map_widget.add_arista('Dakar', 'Abiyan', 100, curvature=0.5, direction="in")
         map_widget.add_arista('Abiyan', 'Lagos', 180, curvature=0.6, direction="in")
         map_widget.add_arista('Lagos', 'Port-Gentil', 70, curvature=0.5, direction="in")
         map_widget.add_arista('Luanda', 'Port-Gentil', 100, curvature=0.7, direction="in")
         map_widget.add_arista('Luanda', 'Walbys bay', 200, curvature=0.7, direction="in")
         map_widget.add_arista('Walbys bay', 'Durban', 200, curvature=0.7, direction="in")
         map_widget.add_arista('Durban', 'Toamasina', 700, curvature=0.7, direction="out")
         map_widget.add_arista('Mombasa', 'Toamasina', 250, curvature=1.2, direction="in")
         map_widget.add_arista('Mombasa', 'Mogadiscio', 250, curvature=0.2, direction="in")
         map_widget.add_arista('Mogadiscio', 'aden', 250, curvature=1.2, direction="in")
         map_widget.add_arista('alexandria', 'aden', 300, curvature=0.1, direction="out")
         map_widget.add_arista('alexandria', 'Atenas', 250, curvature=0.1, direction="out")
         map_widget.add_arista('mascate', 'aden', 250, curvature=0.1, direction="out")
         map_widget.add_arista('mascate', 'dubai', 250, curvature=0.1, direction="out")


        pass

        route = map_widget.a_star(start_port, end_port)
        if route:
            map_widget.animate_route(route)
            map_widget.generate_html(route)
        else:
            print("No se encontró una ruta")
        
        root.mainloop()

    
    threading.Thread(target=run_tkinter).start()

    return "Animación en progreso. Revisa la ventana de Tkinter."

if __name__ == '__main__':
    app.run(debug=True)
