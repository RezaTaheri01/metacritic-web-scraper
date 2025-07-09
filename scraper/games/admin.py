from django.contrib import admin
from .models import Game, Page

# Register your models here.

@admin.register(Game)
class GamesAdmin(admin.ModelAdmin):
    ...
    
    
@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    ...
    
    
