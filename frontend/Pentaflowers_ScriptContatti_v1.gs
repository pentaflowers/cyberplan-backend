/**
 * Pentaflowers — contacts from the mini apps (ElectroPlan, CyberPlan, ...). Version 1.
 *
 * Receives each contact from the mini app servers, writes one row in the "Contatti" tab of this spreadsheet,
 * sends a notification to Pentaflowers and, for CyberPlan, emails the PDF report to the user.
 *
 * Replaces the previous ElectroPlan script. ElectroPlan keeps working unchanged: its rows get Origine = ElectroPlan.
 *
 * BEFORE SAVING: put in SECRET the same value as in the previous script (the same as LEAD_SECRET on Render).
 */

const SECRET = 'COPY_HERE_THE_SECRET_OF_THE_PREVIOUS_SCRIPT';
const NOTIFY_TO = 'pentaflowers@gmail.com';
const TAB = 'Contatti';

const COLUMNS = [
  ['ts', 'Data'], ['source', 'Origine'], ['first_name', 'Nome'], ['last_name', 'Cognome'], ['email', 'Email'],
  ['company', 'Azienda'], ['role', 'Ruolo'], ['country', 'Paese'], ['lang', 'Lingua'],
  ['consent_report', 'Consenso report'], ['updates', 'Consenso ricontatto'], ['consent_ts', 'Data consensi'],
  ['lead_score', 'Punteggio'], ['cra', 'CRA'], ['cra_class', 'Classe CRA'], ['mr', 'Reg. Macchine'],
  ['mr_annex_i_part', 'Allegato I'], ['next_deadline', 'Prossima scadenza'], ['high_gaps', 'Gap priorità alta'],
  ['rules_version', 'Versione regole'], ['report_sent', 'Report inviato'],
];

function doPost(e) {
  let data;
  try {
    data = JSON.parse(e.postData.contents);
  } catch (err) {
    return out_('error');
  }
  if (!data || data.secret !== SECRET) return out_('forbidden');
  try {
    data.source = data.source || 'ElectroPlan';
    if (!data.first_name && data.name) data.first_name = data.name; // ElectroPlan sends a single "name"
    data.report_sent = '';

    if (data.send_report && data.report_pdf_b64 && data.email) {
      const pdf = Utilities.newBlob(Utilities.base64Decode(data.report_pdf_b64), 'application/pdf', data.report_filename || 'CyberPlan_report.pdf');
      MailApp.sendEmail({
        to: data.email, subject: data.mail_subject || 'CyberPlan report', body: data.mail_body || '',
        name: 'Pentaflowers', replyTo: NOTIFY_TO, attachments: [pdf],
      });
      data.report_sent = 'sì';
      notify_(data, pdf);
    } else {
      notify_(data, null);
    }
    appendRow_(data);
    return out_('ok');
  } catch (err) {
    console.error(err);
    return out_('error');
  }
}

function appendRow_(data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(TAB);
  if (!sh) {
    sh = ss.insertSheet(TAB);
    sh.appendRow(COLUMNS.map((c) => c[1]));
    sh.setFrozenRows(1);
  }
  const yes = (v) => (v === true ? 'sì' : v === false ? 'no' : v);
  sh.appendRow(COLUMNS.map((c) => {
    const v = data[c[0]];
    return v === undefined || v === null ? '' : yes(v);
  }));
}

function notify_(d, pdf) {
  const lines = [
    'Origine: ' + d.source,
    'Contatto: ' + [d.first_name, d.last_name].filter(String).join(' ') + ' <' + d.email + '>',
    'Azienda: ' + (d.company || '') + (d.role ? ' · ' + d.role : '') + (d.country ? ' · ' + d.country : ''),
    'Consenso ricontatto: ' + (d.updates === true ? 'sì' : 'no'),
  ];
  if (d.source === 'CyberPlan') {
    lines.push('Punteggio: ' + d.lead_score,
      'CRA: ' + d.cra + (d.cra_class ? ' · ' + d.cra_class : ''),
      'Regolamento Macchine: ' + d.mr + (d.mr_annex_i_part ? ' · parte ' + d.mr_annex_i_part : ''),
      'Prossima scadenza: ' + (d.next_deadline || '-') + ' · gap priorità alta: ' + d.high_gaps,
      'Regole: ' + d.rules_version + ' · report inviato: ' + (d.report_sent || 'no'));
  }
  const opts = { name: 'Pentaflowers mini app' };
  if (pdf) opts.attachments = [pdf];
  MailApp.sendEmail(NOTIFY_TO, 'Nuovo contatto ' + d.source + ' — ' + (d.company || d.email) + (d.lead_score ? ' (' + d.lead_score + ')' : ''), lines.join('\n'), opts);
}

function out_(s) {
  return ContentService.createTextOutput(s).setMimeType(ContentService.MimeType.TEXT);
}

/** Run once from the editor to grant the permissions (sheet + email). It sends a test email to Pentaflowers. */
function authorize() {
  SpreadsheetApp.getActiveSpreadsheet().getName();
  MailApp.sendEmail(NOTIFY_TO, 'Script contatti Pentaflowers: autorizzazioni OK', 'Lo script può scrivere nel foglio e inviare email.');
}
