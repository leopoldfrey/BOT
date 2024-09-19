<h3>L'ultime Bot pour Don Quijote ou Don quixote ou Metamorphy...</h3>
<h4>! Python 3.9.13 !</h4>

<p>les scripts :
  <ul>
    <li><code>install</code> pour installer l'environnement virtuel, sinon utiliser le fichier <code>requirements.txt</code></li>
    <li><code>start Editor</code> pour démarrer l'éditeur</li>
    <li><code>start Bot</code> pour démarrer le bot</li>
  </ul>
  <i>(ils utilisent tous virtualenv, il faut peut-être les modifier pour spécifier la version de python)</i>
</p>

<p>
  Pour utiliser les scripts ps1, il faut installer <a href='https://learn.microsoft.com/fr-fr/powershell/scripting/install/installing-  powershell-on-macos?view=powershell-7.4#installation-via-direct-download' target='_blank'>powershell</a>.<br/>Ça fait la même chose que les scripts shell mais en associant l'extension ps1 avec le terminal (toujours ouvrir avec...), on peut double-cliquer dessus pour démarrer.<br/>
  Et surtout pour le bot où il y a des couleurs c'est plus pratique pour comprendre ce qu'il se passe.<br/>
Et surtout pour l'ordi sous XP c'est nécessaire.  
</p>
<p>
  Dans l'éditeur, en cliquant sur <code>paramètres</code> puis <code>load project</code>, on peut charger un fichier json (typiquement ceux qui sont dans data) ou faire un <code>save as...</code> du projet en cours.<br/>
  On peut y changer la voix, la langue, le modèle mistral...</p>
<p>
  Pour le son, il faut recopier le contenu du répertoire son de Dom Juan, envoi séparé par mail.<br/>
  Il faut aussi créer un répertoire "secret" avec les codes d'api mistal & google, envoi séparé par mail également
</p>
<p>
  <i>Pour l'instant on utilise toujours google pour STT et TTS</i>
</p>
<p>
  Il faut autoriser google à utliser le micro<br/>
  <code>chrome://flags/#unsafely-treat-insecure-origin-as-secure</code>
</p>
