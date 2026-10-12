/**
 * Calendriers {{SECTEUR}} — serveur Apps Script.
 * Les données sont rangées dans les onglets de la feuille Google qui contient ce script :
 * Suivi (statut actuel de chaque adresse), Notes, Historique, Ajouts (adresses ajoutées à la main).
 */

// Code d'accès facultatif : laissez '' pour que le lien suffise, ou mettez par exemple '1832'.
const CODE_ACCES = '';

const STATUTS = { afaire: 'À faire', repasser: 'À repasser', valide: 'Validée' };
const ACTIONS = { statut: 'Statut', note: 'Note', 'note-suppr': 'Note supprimée', ajout: 'Adresse ajoutée' };
const ONGLETS = {
  Suivi: ['Adresse (id)', 'Adresse', 'Statut', 'Par', 'Le'],
  Notes: ['Note (id)', 'Adresse (id)', 'Adresse', 'Texte', 'Par', 'Le'],
  Historique: ['Le', 'Par', 'Adresse (id)', 'Adresse', 'Action', 'De', 'Vers', 'Texte'],
  Ajouts: ['Adresse (id)', 'Numéro', 'Rue', 'Par', 'Le'],
};

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('Calendriers {{SECTEUR}}')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1, viewport-fit=cover');
}

// ---------- Outils ----------
function onglet_(nom) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(nom);
  if (!sh) {
    sh = ss.insertSheet(nom);
    sh.getRange(1, 1, 1, ONGLETS[nom].length).setValues([ONGLETS[nom]]).setFontWeight('bold');
    sh.setFrozenRows(1);
  }
  return sh;
}
function lignes_(nom) {
  const sh = onglet_(nom);
  const n = sh.getLastRow() - 1;
  return n > 0 ? sh.getRange(2, 1, n, ONGLETS[nom].length).getValues() : [];
}
// L'apostrophe force Sheets à garder le texte tel quel : pas de formule (=, +, -, @), pas de conversion en date (12/11) ou en nombre.
function txt_(v, max) {
  const s = String(v == null ? '' : v).trim().slice(0, max);
  return s ? "'" + s : '';
}
const ms_ = (d) => (d instanceof Date ? d.getTime() : Number(d) || 0);
const cle_ = (table, libelle) => Object.keys(table).find((k) => table[k] === libelle) || '';

function verifier_(code) {
  if (CODE_ACCES && String(code || '') !== CODE_ACCES) throw new Error('CODE_ACCES');
}
function nouvelleVersion_() {
  const v = String(Date.now());
  PropertiesService.getScriptProperties().setProperty('version', v);
  return v;
}
function avecVerrou_(fn) {
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try { return fn(); } finally { lock.releaseLock(); }
}

// ---------- Lecture ----------
/** Renvoie tout l'état, ou {same:true} si rien n'a changé depuis la version connue du téléphone. */
function getState(code, versionConnue) {
  verifier_(code);
  const version = PropertiesService.getScriptProperties().getProperty('version') || '0';
  if (versionConnue && versionConnue === version) return { version, same: true };
  return etat_(version);
}

function etat_(version) {
  const suivi = lignes_('Suivi').filter((r) => r[0]).map((r) => ({
    adresse: String(r[0]), statut: cle_(STATUTS, r[2]) || 'afaire', nom: String(r[3]), le: ms_(r[4]),
  }));
  const notes = lignes_('Notes').filter((r) => r[0]).map((r) => ({
    id: String(r[0]), adresse: String(r[1]), texte: String(r[3]), nom: String(r[4]), le: ms_(r[5]),
  }));
  const ajouts = lignes_('Ajouts').filter((r) => r[0]).map((r) => ({
    id: String(r[0]), num: String(r[1]), rue: String(r[2]), nom: String(r[3]), le: ms_(r[4]),
  }));
  const sh = onglet_('Historique');
  const last = sh.getLastRow(), n = Math.min(300, last - 1);
  const hist = n > 0 ? sh.getRange(last - n + 1, 1, n, 8).getValues().reverse().map(hist_) : [];
  return { version, suivi, notes, ajouts, hist };
}
function hist_(r) {
  return {
    le: ms_(r[0]), nom: String(r[1]), adresse: String(r[2]), action: cle_(ACTIONS, r[4]),
    de: cle_(STATUTS, r[5]), vers: cle_(STATUTS, r[6]), texte: String(r[7]),
  };
}

/** Historique complet d'une adresse, du plus récent au plus ancien. */
function getAddrHist(code, adresse) {
  verifier_(code);
  return lignes_('Historique').filter((r) => String(r[2]) === adresse).reverse().slice(0, 100).map(hist_);
}

// ---------- Écritures ----------
function journal_(nom, adresse, libelle, action, de, vers, texte) {
  onglet_('Historique').appendRow([new Date(), txt_(nom, 30), txt_(adresse, 40), txt_(libelle, 120), ACTIONS[action],
    de ? STATUTS[de] : '', vers ? STATUTS[vers] : '', txt_(texte, 120)]);
}

function setStatus(code, adresse, libelle, statut, nom) {
  verifier_(code);
  if (!STATUTS[statut] || !adresse || !String(nom || '').trim()) throw new Error('Données incomplètes');
  return avecVerrou_(() => {
    const sh = onglet_('Suivi');
    const rows = lignes_('Suivi');
    const i = rows.findIndex((r) => String(r[0]) === adresse);
    const de = i >= 0 ? (cle_(STATUTS, rows[i][2]) || 'afaire') : 'afaire';
    if (de !== statut) {
      const ligne = [txt_(adresse, 40), txt_(libelle, 120), STATUTS[statut], txt_(nom, 30), new Date()];
      if (i >= 0) sh.getRange(i + 2, 1, 1, 5).setValues([ligne]); else sh.appendRow(ligne);
      journal_(nom, adresse, libelle, 'statut', de, statut, '');
    }
    return etat_(nouvelleVersion_());
  });
}

function addNote(code, adresse, libelle, texte, nom) {
  verifier_(code);
  if (!adresse || !String(texte || '').trim() || !String(nom || '').trim()) throw new Error('Données incomplètes');
  return avecVerrou_(() => {
    onglet_('Notes').appendRow(['n-' + Utilities.getUuid().slice(0, 8), txt_(adresse, 40), txt_(libelle, 120), txt_(texte, 500), txt_(nom, 30), new Date()]);
    journal_(nom, adresse, libelle, 'note', '', '', texte);
    return etat_(nouvelleVersion_());
  });
}

function delNote(code, noteId, nom) {
  verifier_(code);
  return avecVerrou_(() => {
    const sh = onglet_('Notes');
    const rows = lignes_('Notes');
    const i = rows.findIndex((r) => String(r[0]) === noteId);
    if (i >= 0) {
      if (String(rows[i][4]) !== String(nom || '').trim()) throw new Error('Seul l\'auteur peut supprimer cette note');
      sh.deleteRow(i + 2);
      journal_(nom, String(rows[i][1]), String(rows[i][2]), 'note-suppr', '', '', '');
    }
    return etat_(nouvelleVersion_());
  });
}

function addExtra(code, num, rue, nom) {
  verifier_(code);
  if (!String(num || '').trim() || !String(rue || '').trim() || !String(nom || '').trim()) throw new Error('Données incomplètes');
  return avecVerrou_(() => {
    const id = 'x-' + Utilities.getUuid().slice(0, 8);
    onglet_('Ajouts').appendRow([id, txt_(num, 12), txt_(rue, 80), txt_(nom, 30), new Date()]);
    journal_(nom, id, num + ' ' + rue, 'ajout', '', '', '');
    return etat_(nouvelleVersion_());
  });
}
