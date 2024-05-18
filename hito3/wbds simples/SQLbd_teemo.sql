-- Base de Datos para Teemo Solutions
CREATE DATABASE teemo_bd_navi;
USE teemo_bd_navi;-- uso de la base de datos previamente creada

-- Empezando a Crear las Tablas Identificadas
CREATE TABLE Puertos(
    puertos_id INT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    ubicacion GEOGRAPHY NOT NULL,
    pais VARCHAR(255) NOT NULL,
    capacidad INT
);

CREATE TABLE Navieras(
    navieras_id INT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(50),
    capacidad FLOAT,
    propietario VARCHAR(255),
    estado VARCHAR(50)
);

CREATE TABLE Rutas(
    rutas_id INT PRIMARY KEY,
    distancia FLOAT,
    tiempo_estimado VARCHAR(50),
    nivel_peligrosidad INT,
	puerto_origen_id INT REFERENCES Puertos(puertos_id),
    puerto_destino_id INT REFERENCES Puertos(puertos_id)
);

CREATE TABLE Viajes(
    viajes_id INT PRIMARY KEY,
    fecha_salida VARCHAR(100),
    fecha_llegada VARCHAR(100),
    estado VARCHAR(50),
	naviera_id INT REFERENCES Navieras(navieras_id),
    ruta_id INT REFERENCES Rutas(rutas_id)
);

CREATE TABLE Cargas(
    cargas_id INT PRIMARY KEY,
    descripcion TEXT NOT NULL,
    peso FLOAT,
    tipo VARCHAR(50),
    estado VARCHAR(50),
	viaje_id INT REFERENCES Viajes(viajes_id)
);

CREATE TABLE EventosMaritimos(
    evento_id INT PRIMARY KEY,
    descripcion TEXT NOT NULL,
    fecha TIMESTAMP NOT NULL,
    ubicacion GEOGRAPHY NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    ruta_id INT REFERENCES Rutas(rutas_id),
    viaje_id INT REFERENCES Viajes(viajes_id)
);

-- Insertando Datos