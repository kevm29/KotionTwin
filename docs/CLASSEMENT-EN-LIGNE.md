# Classement en ligne (Supabase)

Les scores sont toujours gardés dans le navigateur du joueur (« Mes meilleurs scores »). Quand `data/online.json`
contient l'URL d'un projet Supabase et sa clé publique `anon`, chaque score est aussi envoyé dans une table partagée
et la page de jeu affiche le « Classement en ligne » : le meilleur score de chaque pseudo, tous joueurs confondus.

## Mise en place (une fois)

1. Créer un projet sur https://supabase.com (formule gratuite).
2. Dans **SQL Editor**, exécuter :

```sql
create table public.scores (
  id bigint generated always as identity primary key,
  game text not null check (game ~ '^[a-z0-9-]{1,64}$'),
  pseudo text not null check (char_length(pseudo) between 2 and 16),
  score bigint not null check (score >= 0 and score < 1000000000000),
  created_at timestamptz not null default now()
);
create index scores_game_score on public.scores (game, score desc);
alter table public.scores enable row level security;
create policy "lecture publique" on public.scores for select to anon using (true);
create policy "ajout public" on public.scores for insert to anon with check (true);
```

3. Recopier dans `data/online.json` l'URL du projet (`https://xxxx.supabase.co`) et la clé **anon public**
   (Project Settings › API). Ne jamais y mettre la clé `service_role`.

## Limites

- Le site est statique : un score est envoyé par le navigateur du joueur, donc un tricheur peut envoyer un faux score.
  Les règles ci-dessus empêchent seulement de modifier ou d'effacer les scores des autres. Pour retirer un faux score :
  Table Editor › `scores` dans Supabase.
- Les pseudos ne sont pas réservés : deux joueurs peuvent choisir le même.
