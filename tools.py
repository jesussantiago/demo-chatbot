import json
import random
import chainlit as cl
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine
from openai import OpenAI
import plotly


draw_plotly_chart_def = {
  "type": "function",
  "function": {
    "name": "draw_plotly_chart",
    "description": "Draws a Plotly chart based on the provided JSON figure and displays it with an accompanying message.",
    "parameters": {
      "type": "object",
      "properties": {
        "message": {
          "type": "string",
          "description": "The message to display alongside the chart"
        },
        "plotly_json_fig": {
          "type": "string",
          "description": "A perfect JSON string without any additional text, this string should be JSON Parseable and should be representing the Plotly figure to be drawn, it must comply with the Plotly JSON schema."
        }
      },
      "required": ["message", "plotly_json_fig"]
    }
  }
}

query_sql_query_def = {
    "type": "function",
    "function": {
        "name": "query_sql_queries",
        "description": "Queries a database using an array of SQL queries to check data related to Progress percentage in Celoxis.",
        "parameters": {
            "type": "object",
            "properties": {
                "sql_queries": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "description": """An array of perfectly well-written Azure SQL TSQL Queries (SELECT statements) to get data from the database.

For aggregation purposes, use functions like SUM, AVG, COUNT, etc. to get the desired results.
If data finding is needed over a string, never use the = (Equal) operator to find data, always use LIKE '%%' except when looking for TI direction.
If a date is involved, always order by the date in ascending order.
Remember that you can't use LIMIT in Azure SQL; use TOP instead.
Do not use other SQL dialects like MySQL, PostgreSQL, etc. Only use TSQL for Azure SQL.


The Personal_completa table is designed to store data about employes  reports within a government’s single-window reporting system. 
Each row represents a unique incident reported by citizens, categorized by type and tracked from its initial report date through resolution. 
This table is essential for analyzing key performance indicators (KPIs) related to incident handling, 
including response time, 
incident frequency, and resolution metrics.

The columns in the Personal_completa table are:
      id_personal (CHAR) : The unique identifier for each employe. This primary key allows each record to be uniquely referenced.
      nombres (NCHAR) : This field allows the names or names of the employes.
      paterno (CHAR) : This field allows the father lastname of the employes.
      materno (CHAR) : This field allows the mother lastname of the employes.
      direccion (CHAR) : The employee address.
      departamento (NCHAR) : The department to which the employee belongs.
      fecha_alta (DATE): The date when employe begin at work.
      fecha_nacimiento(DATE): The employee birthday.
      salario diario (DECIMAL): Daily salary of each employee.
      escolaridad: Education or level of studies that the employee has
      puesto:employee position 


This bajas table seems to be related to employee termination management within an organization. It contains detailed information about employees who have left the company, along with reasons and organizational data.

The columns in the bajas table are:

    id_personal: A unique identifier for the employee who was terminated.
    id_causabaja : A code specific reason for the termination.
    comentarios:  Textual description associated with id_causabaja, which provides a more readable interpretation of the termination reason.
    fechabaja: The date on which the employee was terminated.
    id_area: Identifier for the organizational area the employee belonged to.
    id_depto: Identifier for the department the employee worked in.
    id_empresa: Code representing the company within a corporate group, if applicable.
    id_puesto: Identifier for the position the employee held before termination.
    id_razon_baja: Code specifying the formal reason for the termination.
    razon_baja: Textual description associated with id_razon_baja, which provides a more readable interpretation of the termination reason.
    cb.razon_baja:
    p.celular:employee cellphone
    p.correo_electronico:: email employee
    p.fecha_alta: Date when employee begins at work
    puesto : Textual description associated with id_puesto, which provides a more readable interpretation of the termination reason.
    departamento: employee departament
    sexo: gender , F: female or M:male, M: man or F:women


    The Asistencias table is designed to record and manage attendance and related metrics for employees across an organization. Each row in the table represents a comprehensive attendance record for a specific employee on a particular date, capturing key details about their attendance, absences, and associated benefits or penalties. This table plays a critical role in workforce management, payroll calculations, and compliance reporting.

Key Data Fields:
Employee and Company Information:

id_personal: Unique identifier for the employee whose attendance is being recorded.
id_empresa: Identifier for the company to which the employee belongs.
Attendance and Absence Tracking:

asistencias: Number of attended days or events.
faltas: Number of absences recorded for the employee.
retardos: Number of times the employee arrived late.
permisos: Number of authorized leave permissions granted.
f_incapacidad and incapacidad: Date and type of incapacitation (e.g., medical leave) affecting attendance.
id_tipo_incapacidad: Identifier for the type of incapacity (e.g., illness, accident).
Work Hours and Compensation:

hrsxtras: Total extra hours worked by the employee.
montohx: Monetary compensation for extra hours worked.
montot: Total monetary compensation, including regular and overtime pay.
Additional Attendance Metrics:

puntualidad: Indicates punctuality (e.g., whether the employee meets on-time requirements).
vacacion: Boolean or flag indicating if the record pertains to vacation time.
dias_vacaciones: Number of vacation days taken.
prima: Premium or bonus amount associated with vacation or other incentives.
Administrative Details:

certificado: Reference to any certificates associated with the attendance record (e.g., medical certificates for leave).
asistenciaId: Unique identifier for the attendance record.
fechaMovimiento: Timestamp indicating when the record was created or last updated.
usuario: Identifier for the user or system that made the record entry.
Temporal Information:

fecha: Date of the attendance record.
Usage and Importance:
This table is crucial for:

Payroll Calculations: Determining regular pay, overtime compensation, and bonuses.
Performance Monitoring: Tracking punctuality, absenteeism, and adherence to schedules.
Legal Compliance: Maintaining records of leaves, incapacitations, and overtime in compliance with labor laws.
HR Analytics: Analyzing trends in attendance and identifying areas for policy improvements.
By consolidating detailed attendance data, the Asistencias table serves as a foundation for effective workforce management, ensuring fairness, transparency, and accuracy in handling employee records.  

"""
                    }
                }
            },
            "required": ["sql_queries"],
            "additionalProperties": False,
        }
    }
}



async def query_sql_query_handler(sql_queries: list):





  ORDERS_DB_SERVER="inbestsrv.database.windows.net"
  ORDERS_DB="Recursos_Humanos_Inbest"
  ORDERS_DB_USER="inbestadmin"
  ORDERS_DB_PASSWORD="Sistema.acceso#"

  driver = "ODBC Driver 18 for SQL Server"
  
  connection_string = f"mssql+pyodbc://{ORDERS_DB_USER}:{ORDERS_DB_PASSWORD}@{ORDERS_DB_SERVER}/{ORDERS_DB}?driver={driver}"
  engine = create_engine(connection_string)

  results = []

  # Execute the query
  for query in sql_queries:
    df = pd.read_sql(query, engine)

    if df.size == 1:
      results.append({
        "query": query,
        "result": str(df.iat[0, 0])
      })
    else:
      results.append({
        "query": query,
        "json_result": df.to_json(orient="records")
      })

  return results     
  # return df.to_markdown()  # Return the DataFrame as Markdown


async def draw_plotly_chart_handler(message: str, plotly_json_fig):
  fig = plotly.io.from_json(plotly_json_fig)
  elements = [cl.Plotly(name="chart", figure=fig, display="inline")]

  await cl.Message(content=message, elements=elements).send()

  return "Aquí se muestra el gráfico solicitado."



tools = [
    (query_sql_query_def, query_sql_query_handler),
    (draw_plotly_chart_def, draw_plotly_chart_handler),
]
