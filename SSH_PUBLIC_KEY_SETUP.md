# 🔑 **SSH PUBLIC KEY FÜR HOSTFACTORY ERSTELLEN**

## 🎯 **WARUM SSH KEYS?**
- ✅ **Keine Passwort-Eingabe** bei jedem Login
- ✅ **Sicherer** als Passwörter
- ✅ **Automatisierung** möglich (SCP ohne Passwort)
- ✅ **Branche-Standard** für Server-Zugang

---

## 🔧 **SCHRITT 1: SSH KEY GENERIEREN**

### **💻 AUF DEINEM MAC:**
```bash
# SSH Key Pair erstellen
ssh-keygen -t rsa -b 4096 -C "albert@gashis.ch"

# Wird nach Datei-Name fragen:
# Enter file in which to save the key (/Users/albertgashi/.ssh/id_rsa): 
# → ENTER drücken (Standard-Name verwenden)

# Wird nach Passphrase fragen:
# Enter passphrase (empty for no passphrase):
# → ENTER drücken (kein Passwort für einfacheres Deployment)

# Enter same passphrase again:
# → ENTER drücken
```

### **📋 ERGEBNIS:**
```bash
✅ Private Key: ~/.ssh/id_rsa (GEHEIM - nie teilen!)
✅ Public Key:  ~/.ssh/id_rsa.pub (dieser wird hochgeladen)
```

---

## 🔧 **SCHRITT 2: PUBLIC KEY ANZEIGEN**

### **📖 PUBLIC KEY KOPIEREN:**
```bash
# Public Key anzeigen und kopieren
cat ~/.ssh/id_rsa.pub

# Output sieht so aus:
# ssh-rsa AAAAB3NzaC1yc2EAAAA...sehr_langer_text...== albert@gashis.ch
# → KOMPLETTEN TEXT KOPIEREN (Cmd+A, Cmd+C)
```

---

## 🔧 **SCHRITT 3: KEY ZU HOSTFACTORY HINZUFÜGEN**

### **🌐 HOSTFACTORY CPANEL:**
```bash
1. 🌐 my.hostfactory.ch → Login
2. 🔧 Suche "SSH" oder "Security" oder "Keys"
3. 📝 Klicke "SSH Keys" oder "Public Keys"
4. ➕ "Add New Key" oder "Neuen Schlüssel hinzufügen"
5. 📋 Public Key einfügen (den langen Text)
6. 💾 "Save" oder "Speichern"
```

### **🔍 ALTERNATIVE - CPANEL BEREICHE:**
```bash
SUCHE NACH:
• "SSH Access"
• "Public Keys"
• "Authorized Keys"  
• "Security" → "SSH"
• "Terminal" → "SSH Keys"
```

---

## 🔧 **SCHRITT 4: SSH KEY MANUELL HOCHLADEN (FALLS KEIN CPANEL)**

### **📤 MANUAL UPLOAD VIA SSH:**
```bash
# Einmal mit Passwort einloggen
ssh ftpalbertgashi@server17.hostfactory.ch

# .ssh Ordner erstellen (falls nicht existiert)
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# authorized_keys Datei erstellen
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Key hinzufügen (Public Key hier einfügen!)
echo "ssh-rsa AAAAB3NzaC1yc2EAAAA...DEIN_PUBLIC_KEY_HIER...== albert@gashis.ch" >> ~/.ssh/authorized_keys

# Ausloggen
exit
```

---

## 🧪 **SCHRITT 5: SSH KEY TESTEN**

### **🔗 PASSWORT-LOSER LOGIN TESTEN:**
```bash
# Sollte OHNE Passwort funktionieren!
ssh ftpalbertgashi@server17.hostfactory.ch

# Falls es funktioniert → ✅ SUCCESS!
# Falls Passwort verlangt wird → Schritt 4 wiederholen
```

---

## 🚀 **SCHRITT 6: DEPLOYMENT MIT SSH KEYS**

### **📤 JETZT OHNE PASSWORT-EINGABE:**
```bash
# Frontend hochladen (kein Passwort!)
scp -r frontend/build/* ftpalbertgashi@server17.hostfactory.ch:~/htdocs/

# Backend hochladen (kein Passwort!)
scp backend/server_gashis.py ftpalbertgashi@server17.hostfactory.ch:~/htdocs/api/server.py
scp backend/requirements_simple.txt ftpalbertgashi@server17.hostfactory.ch:~/htdocs/api/requirements.txt

# SSH Login (kein Passwort!)
ssh ftpalbertgashi@server17.hostfactory.ch
```

---

## 🔍 **TROUBLESHOOTING:**

### **❌ PROBLEM: SSH Key wird nicht akzeptiert**
```bash
LÖSUNG 1: Permissions prüfen
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

LÖSUNG 2: SSH Config Debug
ssh -v ftpalbertgashi@server17.hostfactory.ch
# → Zeigt Debug-Info warum Key nicht funktioniert

LÖSUNG 3: Hostfactory Support fragen
# Falls cPanel keine SSH Key Option hat
```

### **❌ PROBLEM: Permission denied (publickey)**
```bash
LÖSUNG: Key ist nicht richtig installiert
# Schritt 4 wiederholen
# Kompletten Public Key kopieren (inklusive ssh-rsa und Email)
```

---

## 💡 **HOSTFACTORY-SPEZIFISCHE TIPPS:**

### **📋 CPANEL BEREICHE ZU SUCHEN:**
```bash
🔍 HAUPTMENÜ:
• "Advanced" → "SSH Access"
• "Security" → "SSH Keys"  
• "Files" → "SSH Keys"

🔍 SUCHFELD:
• "ssh"
• "keys"
• "security"
```

### **📧 FALLS NICHT GEFUNDEN:**
```bash
📞 Hostfactory Support kontaktieren:
• Tel: +41 44 637 40 40
• Email: support@hostfactory.ch
• Frage: "Wo kann ich SSH Public Keys hinzufügen?"
```

---

## 🎯 **READY TO START?**

### **1️⃣ SSH KEY GENERIEREN:**
```bash
ssh-keygen -t rsa -b 4096 -C "albert@gashis.ch"
```

### **2️⃣ PUBLIC KEY KOPIEREN:**
```bash
cat ~/.ssh/id_rsa.pub
```

### **3️⃣ ZU HOSTFACTORY HINZUFÜGEN:**
```bash
my.hostfactory.ch → SSH Keys → Add Key
```

**Soll ich dir beim ersten Schritt helfen?** 🔑
