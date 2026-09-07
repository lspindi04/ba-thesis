from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from docx import Document
from docx.shared import Inches
from PIL import Image
import tempfile

base = Path(r"C:\zenlab-Projects\ba-thesis\implementation-concept")
src = base / "DeviceIntegrationPlugin_Kurzkonzept.docx"
out = base / "DeviceIntegrationPlugin_Kurzkonzept_geprueft.docx"
diagrams = base / "diagrams"

doc = Document(src)

paragraph_replacements = {
    "Die bestehenden DeviceAgents bleiben für Hardwarekommunikation, Geräteprotokolle und TreeNode-Funktionen verantwortlich. Der AgentManager startet und verwaltet diese Prozesse. Der bereits entwickelte ServiceForwardRouter überträgt Aufträge und Antworten, besitzt jedoch noch keine vollständige Unterstützung für mehrere dynamisch registrierte und explizit adressierte Integrationen.":
    "Die konkreten DeviceAgents bleiben für Hardwarekommunikation, Geräteprotokolle und TreeNode-Funktionen verantwortlich. Der AgentManager startet und überwacht nur noch deren Prozesse. Das im Showcase als mehrere Klassen vorhandene Service-Forward-Routing-Subsystem überträgt Aufträge und Antworten, unterstützt aber noch keine saubere Trennung mehrerer dynamisch registrierter Service-Sessions.",
    "Das neue DeviceIntegrationPlugin soll diese Lücke schließen. Es verwaltet aktive Integrationen und deren Devices, überwacht deren Lebenszyklus und vermittelt Aufträge sowie Wertänderungen zwischen Clients und DeviceAgents.":
    "Das neue DeviceIntegrationPlugin schließt diese Lücke. Es verwaltet aktive Integrationen und ihre Devices, überwacht deren Lebenszyklus, hostet Client- und Agent-Service und vermittelt TreeNode-Aufträge sowie Ereignisse über genau eine bidirektionale Verbindung je Registrierung.",
    "Der Integration Adapter registriert sich über den DeviceIntegrationAgentServiceProxy beim DeviceIntegrationAgentService und sendet RequestedServiceId, Metadaten, Version und vollständige Device-Liste.":
    "Der DeviceIntegrationAgentRuntime registriert sich über den DeviceIntegrationAgentServiceProxy beim DeviceIntegrationAgentService und sendet RequestedServiceId, Metadaten sowie die vollständige aktuelle Device-Liste.",
    "Der DeviceIntegrationAgentService validiert die ID, registriert den Worker im ServiceForwardRouter und erzeugt ServiceIdentification sowie RegistrationId.":
    "Der DeviceIntegrationAgentService validiert und reserviert die ServiceId, erzeugt eine RegistrationId und hält die Registrierung zunächst im Zustand Connecting. Erst wenn die Duplex-Verbindung eindeutig angenommen und alle neun Request-Pumps bereit sind, wird sie atomar auf Active gesetzt und für Clients sichtbar.",
    "NotifyDeviceList ersetzt den Device-Snapshot atomar und erneuert die Lease.":
    "NotifyDeviceList enthält immer die vollständige aktuelle Device-Liste, ersetzt den Snapshot atomar und erneuert zugleich die Lease. Ein separates Agent-KeepAlive gibt es nicht.",
    "Nach UpdateInterval plus Tolerance werden Devices, Streams und Subscriptions entfernt.":
    "Bleibt NotifyDeviceList länger als UpdateInterval plus Tolerance aus, prüft die Registry LeaseRevision und Zeitstempel erneut atomar. Nur dann werden Verbindung, wartende Jobs, Devices und Subscriptions über denselben idempotenten SessionTerminator entfernt.",
    "Cleanup prüft die RegistrationId, damit ein alter Timeout keine neue Verbindung entfernt.":
    "Jeder Frame und jeder Cleanup prüft die RegistrationId, damit ein alter Stream oder Timeout niemals eine neuere Verbindung mit gleicher ServiceId verändert.",
    "public record ServiceIdentification(string Id);\n\npublic record RoutedJobRequest<T>(\n    ulong JobId,\n    ServiceIdentification Target,\n    Guid RegistrationIdSnapshot,\n    T Parameter);\n\npublic record RoutedJobResult<T>(\n    ulong JobId,\n    ServiceIdentification Source,\n    Guid RegistrationIdSnapshot,\n    bool Succeeded,\n    T? Value,\n    ExceptionDto? Error);":
    "public sealed class JobRequest<T>\n{\n    public ulong JobId { get; init; }\n    public ServiceIdentification Service { get; init; }\n    public Guid RegistrationId { get; init; }\n    public string SerializedParameter { get; init; }\n    [IgnoreDataMember] public T? Parameter { get; init; }\n}\n\npublic sealed class JobResult<T>\n{\n    public ulong JobId { get; init; }\n    public ServiceIdentification Service { get; init; }\n    public Guid RegistrationId { get; init; }\n    public bool Succeeded { get; init; }\n    public string SerializedValue { get; init; }\n    public ExceptionDto? Exception { get; init; }\n    [IgnoreDataMember] public T? Value { get; init; }\n}",
    "Die WebAPI verwendet IDeviceIntegrationClientService; zur Laufzeit übernimmt der DeviceIntegrationClientServiceProxy den gRPC-Aufruf.":
    "Die bestehende WebAPI verwendet weiterhin IMediator, ITreeNodeBasedDeviceManagement und IDeviceCollectionContainer. Ein späterer, ausdrücklich als Low Priority markierter Adapter implementiert diese vorhandenen Interfaces und verwendet intern den DeviceIntegrationClientServiceProxy.",
    "Der Integration Adapter verwendet IDeviceIntegrationAgentService; zur Laufzeit übernimmt der DeviceIntegrationAgentServiceProxy Registrierung, Streams und Rückmeldungen.":
    "Der DeviceIntegrationAgentRuntime besitzt und disposed den DeviceIntegrationAgentServiceProxy. Er registriert sich, öffnet genau einen bidirektionalen Stream, multiplexed darin Jobs, Resultate und Events und meldet parallel vollständige Device-Snapshots.",
    "DeviceIntegrationClientService und DeviceIntegrationAgentService laufen im Plugin und teilen Registry, Subscription-Verwaltung und ServiceForwardRouter.":
    "DeviceIntegrationClientService und DeviceIntegrationAgentService laufen im Plugin. Sie greifen ausschließlich über Lifecycle-, Dispatcher-, Connection- und Subscription-Abstraktionen auf die gemeinsam als SingleInstance registrierten Zustände zu.",
    "Device-spezifischer Code bleibt unverändert in den bestehenden DeviceAgents.":
    "Gerätespezifische Protokolle und TreeNode-Logik bleiben in den bestehenden DeviceAgents. Die gemeinsame Management-Basis beziehungsweise der DeviceAgent-Composition-Root muss jedoch vom alten DeviceManagementPlugin entkoppelt werden.",
    "Ausbleibender Heartbeat führt genau einmal zum vollständigen Cleanup.":
    "Eine ausbleibende vollständige NotifyDeviceList-Meldung führt nach Intervall plus Toleranz genau einmal zum vollständigen Cleanup.",
    "Ein bestehender DeviceAgent wird ohne Änderung seiner Gerätekommunikation über den Adapter angebunden.":
    "Ein bestehender DeviceAgent wird ohne Änderung seiner Gerätekommunikation angebunden; nur gemeinsame Basis beziehungsweise Composition Root werden angepasst.",
    "Abbildung 5: Registrierung, Heartbeat, Reconnect und Cleanup (PlantUML)":
    "Abbildung 5: Registrierung, Aktivierungsbarriere, Vollsnapshot-Lease, Neuregistrierung und Cleanup (PlantUML)",
    "Diese Sicht beschreibt, wie eine Client-Anwendung über den unveränderten TreeNodeBasedClient auf Services und Devices zugreift. Das Plugin löst das Ziel auf und leitet die Operation über den DeviceIntegrationAgentServiceProxy an den passenden DeviceAgent weiter.":
    "Diese Sicht beschreibt, wie eine Client-Anwendung über den unveränderten TreeNodeBasedClient auf Integrationen und Devices zugreift. Das Plugin löst DeviceId und aktive ServiceSession auf; der Auftrag erreicht den Agent über dessen bereits geöffneten bidirektionalen gRPC-Stream.",
    "EMPFOHLENE FREIGABE  Zuerst den Unicast-MVP freigeben. Broadcast, vollständige Subscription-Typen und Gateway werden als priorisierte Erweiterungen behandelt. Dadurch bleibt die Bachelorarbeit innerhalb eines realistischen Umfangs und besitzt trotzdem einen klaren technischen Eigenbeitrag.":
    "EMPFOHLENE FREIGABE  Ein vertikaler Unicast-Durchstich ist der erste Zwischenmeilenstein. Zum MVP gehören danach Registrierung, Vollsnapshot-Lease, eine Duplex-Verbindung, Target/Broadcast/Aggregation und Node-Streams einschließlich ChildNodeAdded/Removed. Gateway und WebAPI-Adapter bleiben optionale Folgearbeiten.",
}

# Das Codebeispiel im Ausgangsdokument endet mit einem zusätzlichen Zeilenumbruch.
# Deshalb wird es hier inhaltlich statt über vollständige Stringgleichheit adressiert.
for _key in list(paragraph_replacements):
    if "RoutedJobRequest" in _key:
        paragraph_replacements[_key] = """public readonly record struct ServiceSessionKey(
    string ServiceId, Guid RegistrationId);

public enum JobResultKind { Response, Event }

public sealed class JobRequest<T>
{
    public ulong JobId { get; init; }
    public ServiceSessionKey Target { get; init; }
    public string SerializedParameter { get; init; }
    [IgnoreDataMember] public T? Parameter { get; init; }
}

public sealed class JobResult<T>
{
    public ulong JobId { get; init; }
    public ServiceSessionKey Source { get; init; }
    public JobResultKind Kind { get; init; }
    public bool Succeeded { get; init; }
    public string SerializedValue { get; init; }
    public ExceptionDto? Exception { get; init; }
    [IgnoreDataMember] public T? Value { get; init; }
}"""

cell_replacements = {
    "EMPFOHLENE FREIGABE  Zuerst den Unicast-MVP freigeben. Broadcast, vollständige Subscription-Typen und Gateway werden als priorisierte Erweiterungen behandelt. Dadurch bleibt die Bachelorarbeit innerhalb eines realistischen Umfangs und besitzt trotzdem einen klaren technischen Eigenbeitrag.":
    "EMPFOHLENE FREIGABE  Ein vertikaler Unicast-Durchstich ist der erste Zwischenmeilenstein. Zum MVP gehören danach Registrierung, Vollsnapshot-Lease, eine Duplex-Verbindung, Target/Broadcast/Aggregation und Node-Streams einschließlich ChildNodeAdded/Removed. Gateway und WebAPI-Adapter bleiben optionale Folgearbeiten.",
    "Registrierung, Heartbeat, Unicast-Routing, TreeNode-Adapter und automatisierte Tests.":
    "Registrierung, NotifyDeviceList-Vollsnapshot, eine Duplex-Verbindung, Unicast-/Broadcast-Routing, TreeNode-Anbindung und automatisierte Tests.",
    "Device-Snapshot und Heartbeat verarbeiten": "vollständige Device-Liste als Lease-Signal verarbeiten",
    "Broadcast an alle Integrationen": "Produktionsreife bidirektionale Gateway-Laufzeit",
    "Unicast-Aufträge an einen Service routen": "Unicast- und Broadcast-Aufträge routen und Ergebnisse aggregieren",
    "Vollständige Gateway-Implementierung": "Feingranulare Autorisierung und Security-Härtung",
    "Serverseitiger gRPC-Service im Plugin für TreeNode-Aufrufe, Device-Abfragen und Client-Streams.":
    "Serverseitiger gRPC-Service im Plugin für TreeNode-Aufrufe, einen Stream je konkreter Node-Subscription sowie einen getrennten Registry-Eventstream.",
    "Serverseitiger gRPC-Service im Plugin für Registrierung, Heartbeat, Job-Stream und Ergebnisse.":
    "Serverseitiger gRPC-Service im Plugin für Registrierung, vollständige Device-Listen, Abmeldung und genau einen bidirektionalen Stream für Jobs, Resultate und Events.",
    "Verwaltet Device-zu-Service-Zuordnung, Registrierungen und Lebenszyklus.":
    "Verwaltet Device-zu-ServiceSession-Zuordnung, Registrierungen und die durch NotifyDeviceList erneuerte Lease.",
    "Enthält Zielrouting, Job-Korrelation, Timeouts und Streams; kein zusätzlicher Integration Router.":
    "Bezeichnet das Subsystem aus JobFacade, JobTransmitter, JobRequestFactory und Hilfsklassen; es wird vollständig aus AgentManager herausgelöst und um Multi-Service-Routing erweitert.",
    "Verwendet den AgentServiceProxy und adaptiert Aufträge an ITreeNodesBasedDeviceAgent.":
    "Orchestriert AgentServiceProxy, Duplex-Stream, WorkRunner, EventForwarder und die vorhandenen Interfaces ITreeNodesBasedDeviceAgent sowie IMultipleDevicesAgent.",
    "ServiceForwardRouterPlugin.Common.Contracts": "ServiceForwardRouter.Core.Contracts",
    "ServiceForwardRouterPlugin.Common": "ServiceForwardRouter.Core",
    "DeviceIntegrationPlugin.Contracts": "DeviceIntegration.Contracts",
    "DeviceIntegrationPlugin.Core": "DeviceIntegration.Plugin.Core",
    "DeviceIntegrationPlugin.IntegrationClient": "DeviceIntegration.AgentSdk",
    "DeviceIntegrationPlugin.Tests": "DeviceIntegration.Tests",
    "Zielrouting, JobFacade, Transmitter, Korrelation, Timeout und Broadcast.": "JobFacade, async Transmitter, ServiceSession-Routing, Target, Broadcast, Aggregation und Eventstreams.",
    "ClientService, AgentService, Device Registry, LeaseMonitor und Subscription-Verwaltung.": "Registry, Lifecycle, SessionTerminator, Connections, Dispatcher, Services und Subscription-Verwaltung.",
    "Integration Adapter auf Basis des DeviceIntegrationAgentServiceProxy für bestehende DeviceAgents.": "AgentRuntime, SmartProxy, Outbox, WorkScheduler, Mapper sowie Snapshot- und Event-Bridge für bestehende DeviceAgents.",
    "Reconnect": "Streamverlust / Neuregistrierung",
    "Timeout, Reconnect und Deregistrierung behandeln": "Timeout, Streamverlust, Neuregistrierung und Deregistrierung behandeln",
    "TreeNode-Aufrufe über Adapter ausführen": "TreeNode-Aufrufe und Node-Streams einschließlich ChildNodeAdded/Removed ausführen",
    "Common- und Contracts-Projekte entkoppeln; AgentManager auf neue Referenzen umstellen.":
    "Routing- und Contracts-Projekte in den DeviceIntegrationPlugin-Bereich verschieben; alte Router-, Proxy-, Service- und Worker-Verweise aus AgentManager entfernen.",
    "ServiceIdentification, geroutete Envelopes, RouteRegistry und RouteResolver implementieren.":
    "ServiceIdentification, ServiceSessionKey, MultiServiceJobTransmitter, Zielrouting, Broadcast und Aggregation implementieren.",
    "Duplex Worker und Adapter für ITreeNodesBasedDeviceAgent implementieren.":
    "Genau eine Duplex-Verbindung, MessageCodec, WorkRunner und Anbindung an ITreeNodesBasedDeviceAgent/IMultipleDevicesAgent implementieren.",
    "Heartbeat, Timeout, Reconnect und Unregister gleichzeitig.":
    "NotifyDeviceList, Timeout, Streamende, vollständige Neuregistrierung und Unregister gleichzeitig.",
    "Empfehlung: einfacher ValueChanged-Fall im MVP; ChildAdded/Removed als Erweiterung.":
    "ValueChanged sowie SubscriptionCreated/Disposed gehören zum MVP. ChildNodeAdded/Removed sind laut Ausgangskonzept ebenfalls Pflicht und benötigen eine verbindliche Erweiterung der gemeinsamen Tree-/Container-Basis.",
    "Empfehlung: konzipieren, aber erst nach stabilem Unicast-MVP implementieren.":
    "Broadcast und Ergebnisaggregation gehören zum Router-Kern; das Gateway wird konzipiert und nur bei ausreichendem Zeitbudget implementiert.",
    "Bestehende AgentManager-Nutzung soll nach Extraktion weiterhin bauen und funktionieren.":
    "AgentManager soll nach der Migration nur Prozessstart und -überwachung leisten. Dafür müssen die heute routergebundenen DeviceRunner-, DeviceProvider-, AgentProvider-, AgentInformationProvider- und ConfigurationEditor-Service-/Worker-/Proxy-Pfade entfernt oder routerfrei ersetzt werden.",
    "Zuerst den Unicast-MVP freigeben. Broadcast, vollständige Subscription-Typen und Gateway werden als priorisierte Erweiterungen behandelt. Dadurch bleibt die Bachelorarbeit innerhalb eines realistischen Umfangs und besitzt trotzdem einen klaren technischen Eigenbeitrag.":
    "Ein vertikaler Unicast-Durchstich ist der erste Zwischenmeilenstein. Zum MVP gehören danach Registrierung, Vollsnapshot-Lease, eine Duplex-Verbindung, Target/Broadcast/Aggregation und Node-Streams einschließlich ChildNodeAdded/Removed. Gateway und WebAPI-Adapter bleiben optionale Folgearbeiten.",
}

def replace_paragraph_text(paragraph, mapping):
    text = paragraph.text
    lookup = text if text in mapping else text.rstrip()
    if lookup not in mapping:
        return False
    new_text = mapping[lookup]
    if paragraph.runs:
        paragraph.runs[0].text = new_text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(new_text)
    return True

for p in doc.paragraphs:
    replace_paragraph_text(p, paragraph_replacements)
    # Das Ausgangsdokument setzte vor fast jedem Hauptabschnitt einen manuellen
    # Seitenumbruch. Das erzeugte mehrere halbleere beziehungsweise eine ganz leere
    # Seite. Word darf den kompakten Brief stattdessen natürlich umbrechen.
    for br in p._p.xpath('.//w:br[@w:type="page"]'):
        br.getparent().remove(br)

for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                replace_paragraph_text(p, cell_replacements)

# Neue Bilder im selben Seitenrahmen, aber ohne Verzerrung.
image_paths = [
    diagrams / "01_komponenten.png",
    diagrams / "02_hauptablauf.png",
    diagrams / "03_kernmodell.png",
    diagrams / "04_usecase_uebersicht.png",
    diagrams / "05_usecase_integration.png",
    diagrams / "06_usecase_client.png",
]
max_boxes = [(6.1, 4.3), (6.1, 4.4), (6.1, 2.5), (4.0, 7.0), (5.6, 6.3), (4.0, 6.7)]
for shape, img_path, (max_w, max_h) in zip(doc.inline_shapes, image_paths, max_boxes):
    with Image.open(img_path) as im:
        ratio = im.width / im.height
    width = min(max_w, max_h * ratio)
    height = width / ratio
    shape.width = Inches(width)
    shape.height = Inches(height)

staged = base / ".render" / "staged_checked.docx"
doc.save(staged)
replacements = {f"word/media/image{i}.png": path.read_bytes() for i, path in enumerate(image_paths, 1)}
with ZipFile(staged, "r") as zin, ZipFile(out, "w", ZIP_DEFLATED) as zout:
    for info in zin.infolist():
        data = replacements.get(info.filename, zin.read(info.filename))
        zout.writestr(info, data)

print(out)
