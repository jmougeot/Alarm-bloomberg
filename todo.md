Je veux utilser une interface graphique : PySide6 (Qt) + PyQtGraph : Gestion du temps réel (CRUCIAL)
L'objectif est de créer un monitor de prix sur des strtégies comme (butterfly, condor, etc ...) et plusieur à la fois: 
Il y a donc un bloc pour chaque strtégy :
voici la compositiond de chaque bloc : 
- une ligne avec  (Code de l'indice ex : SFRH6C 98.00) un bloc ou on peut choisir (long ou short)
- Pouvoir ajouter une ligne ou ne supprimer
- Le prix en direct de la stratégie (il suffit de faire un calcul ou on additionne les prix des deiffernts options vanilles )
- Le prix cible (+ ou - un intervalle de prix )
- Un status (en cours, fais)
- pouvoir supprimer la stratégie

Je veux pouvoir ajouter le nombre de bloc que je veux en peranance cad si je fais tourner le code pendnat une heure : et bien je veux pouvoir modifier un bloc ou en ajouter et que tout soit automatique

J'ai deja implementé un syteme d'event dans le dossier bloomberg , hesite pas à l'utilser  