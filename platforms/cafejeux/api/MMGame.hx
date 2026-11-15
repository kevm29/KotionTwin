/*
 * KotionTwin — interface des jeux CaféJeux, recréée (l'original, ../api, n'est pas dans l'archive).
 * Volontairement vide : le conteneur (Main.hx) appelle les méthodes du jeu dynamiquement
 * (initialize, onMessage, onTurnDone, onVictory, onReconnectDone, main), car les jeux
 * ne déclarent pas tous les mêmes signatures.
 */
interface MMGame<Msg> {
}
