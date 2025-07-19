
from django.db import models

class Noticia(models.Model):
    titulo = models.CharField(max_length=255)
    autor = models.CharField(max_length=100)
    cuerpo = models.TextField()
    fecha_publicacion = models.DateTimeField()

    def __str__(self):
        return self.titulo
