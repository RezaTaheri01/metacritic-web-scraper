from django.views.generic import ListView
from .models import Game
from django.db.models import Case, When, Value, IntegerField, Q


class GamesListView(ListView):
    template_name = 'games/games.html'
    model = Game
    # change name to the same name in filter category class to use both :)
    context_object_name = 'games'
    allow_empty = True
    paginate_by = 24  # games/?page=<page-number> Structure

    def get_queryset(self):
        search_text = self.request.GET.get('search', '').strip()
        games = super().get_queryset()

        if not search_text:
            return games.order_by('-meta_score')

        return games.annotate(
            relevance=Case(
                When(title__iexact=search_text, then=Value(3)),
                When(title__icontains=search_text, then=Value(2)),
                When(slug__icontains=search_text, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).filter(
            Q(title__icontains=search_text) | Q(slug__icontains=search_text)
        ).order_by('-relevance', '-meta_score')
