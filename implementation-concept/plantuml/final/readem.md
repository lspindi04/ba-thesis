# Sprechzettel zum aktuellen Diagrammstand

Der beste Einstieg ist:

> „Mein Ziel ist eine einheitliche Integrationsgrenze für Geräte. Der bestehende Client bleibt unverändert. Das DeviceIntegrationPlugin nimmt Client-Aufrufe entgegen und routet sie über bestehende Methodenstreams zu einer konkreten Integration. Deren interne Umsetzung ist nicht Teil des aktuellen Scopes.“

## 00 – Gesamtarchitektur

> „Der bestehende `TreeNodeBasedClient` bleibt unverändert. Der spätere ASP.NET-Core-Adapter übersetzt seine Aufrufe mithilfe eines SmartProxys in gRPC-Aufrufe und bleibt zunächst außerhalb meines Scopes.“

> „Das generische Routing wird nach iCore verschoben. Dort kennt es Services, Jobs, Ergebnisse und generische Events, aber keine Devices und keine konkrete Integrationsarchitektur.“

Das `DeviceIntegrationPlugin` ergänzt darüber die gerätespezifischen Aufgaben:

- veröffentlichte Devices verwalten,
- Device-IDs auf die zuständige Integration auflösen,
- Integrationsstreams beobachten,
- Integrationen aktivieren und deaktivieren,
- Device-Events an Clients verteilen.

## Global eindeutige Namen

Mit „Global Naming“ ist in diesem Konzept kein Naming-Service gemeint. Es ist eine Clean-Code-Regel:

> „Ein neuer Typ soll bereits an seinem Namen eindeutig erkennbar sein und nicht erst zusammen mit seinem Namespace verständlich werden.“

Deshalb verwenden die neuen Typen fachliche Hauptwörter statt eines pauschalen Präfixes:

- `IntegrationDeviceCatalog` bezeichnet den Katalog der integrierten Devices,
- `IntegrationDeviceId` bezeichnet die zusammengesetzte Geräteidentität,
- `IntegrationStreamTracker` bezeichnet die Überwachung der Integrationsstreams,
- `IntegrationLifecycleCoordinator` bezeichnet die Lifecycle-Koordination,
- `DeviceNodeValueDto` bezeichnet den Wert eines Device-Nodes.

Der Präfix `DeviceIntegration` bleibt nur bei den etablierten Einstiegspunkten wie `DeviceIntegrationService`, `DeviceIntegrationHost` und `DeviceIntegrationWorker` erhalten.

Bestehende Routingnamen wie `JobFacade`, `JobTransmitter` und `ServiceDirectory` bleiben unverändert, weil dieses Routing lediglich verschoben und nicht fachlich neu entworfen wird.

## 03 – Routing Execution und Events

> „Der bestehende `WorkRunner` verarbeitet normale Request-Response-Aufträge. Er liest eine `JobRequest`, führt die übergebene Funktion aus und erzeugt ein korreliertes `JobResult`.“

Beim `EventWorkRunner` ist wichtig:

> „Die SubscribeRequests sind bereits `JobRequest<EmptyDto>` und enthalten eine `ServiceIdentification`. Der EventWorkRunner merkt sich beim ersten Subscribe diese Service-ID und übernimmt sie später in `JobResult.Service`. Die Signatur der EventWorkRunnerFactory bleibt unverändert.“

Die `JobId` bleibt der Handle für Subscribe und Unsubscribe. Ein späteres Event ist keine direkte Antwort auf den Subscribe-Job.

## 04 – Identitäten

Die globale Geräteidentität entsteht weiterhin aus:

```text
ServiceIdentification + LocalDeviceId
```

Beide Werte stehen in `IntegrationDeviceId`. Gleiche lokale Device-IDs sind in unterschiedlichen Integrationen erlaubt. Innerhalb derselben Integration muss die `LocalDeviceId` eindeutig sein.

Die `ConnectionId` gehört dagegen nur zu einem konkreten Verbindungsaufbau und wird bei einem vollständigen Reconnect neu erzeugt.

## 05a – Plugin-Services und Routing

> „Die gRPC-Services bleiben dünn. Sie delegieren an interne Komponenten und enthalten weder eigene Queues noch ein zweites Routing.“

Der `DeviceIntegrationService` verwendet den `IntegrationDeviceCatalog`:

```text
ReadValue(IntegrationDeviceId)
→ IntegrationDeviceCatalog.ResolveService
→ ServiceIdentification
→ JobFacade sendet gezielt an den Service
```

`GetDevices` liest die bereits veröffentlichten Devices aus dem `IntegrationDeviceCatalog` und führt nicht bei jedem Client-Aufruf einen Broadcast aus.

Der `DeviceIntegrationWorkerService` reicht die vorhandenen Request-Streams der `JobTransmitter` über gRPC weiter. Die `Send...Result`-Methoden melden Ergebnisse beim passenden Transmitter.

## 05b – Plugin-Lifecycle und Events

### IntegrationStreamTracker

> „Der `IntegrationStreamTracker` baut keine Streams auf. Er beobachtet nur die Methodenstreams, die sowieso für das Routing benötigt werden.“

Er merkt sich:

```text
ServiceIdentification
ConnectionId
geöffnete Pflichtstreams
```

Der Tracker bleibt im `DeviceIntegrationPlugin`, weil er die konkreten Device-Integration-Streams kennt.

### IntegrationLifecycleCoordinator

> „Der LifecycleCoordinator führt Aktivierung und Deaktivierung aus. Dadurch bleibt der StreamTracker ein kleiner technischer Zustandsverwalter.“

Aktivierung:

1. Alle Pflichtstreams sind geöffnet.
2. Service im Routing registrieren.
3. Vollständigen `GetDevices`-Snapshot abrufen.
4. Globale Event-Subscription starten.
5. Snapshot im `IntegrationDeviceCatalog` veröffentlichen.

Deaktivierung:

1. Event-Subscription stoppen.
2. Devices dieser Service-ID entfernen.
3. Service aus dem Routing entfernen.
4. Übrige Streams dieser Connection-ID abbrechen.

### IntegrationDeviceCatalog und ServiceDirectory

> „Die `ServiceDirectory` ist die einzige Quelle für verbundene und routbare Services. Der `IntegrationDeviceCatalog` enthält keine zweite ActiveIntegrations-Liste. Er speichert nur veröffentlichte Devices und deren Service-Zuordnung.“

```text
ServiceDirectory
└── Welche Integrationen sind verbunden?

IntegrationDeviceCatalog
└── Welche Devices sind veröffentlicht und zu welchem Service gehören sie?
```

### IntegrationEventSubscriptionManager und DeviceEventHub

> „Pro verbundener Integration gibt es nur eine Remote-Event-Subscription. Mehrere Clients führen nicht zu mehreren Streams zur Integration.“

Der `DeviceEventHub` verteilt eingehende Events lokal an beliebig viele Client-Subscriptions.

## 06 – Integration SDK

> „Das SDK definiert mit `IDeviceIntegration` den fachlichen Vertrag. Es übernimmt die wiederkehrende technische Logik für SmartProxy, Methodenstreams, Worker, Events, Connection-IDs und Reconnects.“

Die Beispielintegration implementiert nur:

- `GetDevices`,
- `GetNodeInfo`,
- `ReadValue`,
- `WriteValue`,
- `ExecuteCommand`,
- `IntegrationEvent`.

Ihre interne Struktur wird bewusst nicht betrachtet. Insbesondere ist der AgentManager kein Bestandteil des aktuellen Scopes.

Der `IntegrationWorkerSupervisor` beendet bei einem unerwarteten Pflichtstream-Abbruch alle Worker derselben `ConnectionId` und verbindet anschließend vollständig mit einer neuen `ConnectionId`.

## 07 – Integration-Lifecycle

### Connecting

Alle Pflichtstreams werden mit derselben `ConnectionId` geöffnet. Ein Connect-Timeout verhindert dauerhaft unvollständige Verbindungen.

### RoutingReady

Der Service ist bereits in der `ServiceDirectory` registriert, damit der initiale `GetDevices`-Job gezielt geroutet werden kann. Für Clients sind noch keine Devices veröffentlicht.

### Active

Erst nach erfolgreichem Snapshot und gestarteter Event-Subscription wird der Snapshot im `IntegrationDeviceCatalog` veröffentlicht. Eine zusätzliche Liste aktiver Integrationen wird nicht benötigt.

### Terminating

Endet ein Pflichtstream, werden Event-Subscription, Devices, Route und restliche Streams derselben Verbindung entfernt. Eine verspätete Beendigung einer alten `ConnectionId` darf eine neue Verbindung nicht beeinflussen.

Es gibt keinen zusätzlichen fachlichen Heartbeat- oder Lifecycle-Stream. Transportseitiges HTTP/2- beziehungsweise gRPC-Keep-Alive kann trotzdem tote Netzwerkverbindungen erkennen.

## 08 – Device-Lifecycle

> „Der Integration-Lifecycle beschreibt die Erreichbarkeit einer ganzen Integration. Der Device-Lifecycle beschreibt die Verfügbarkeit einzelner Devices innerhalb dieser Integration.“

Meldet die Integration `DeviceRemoved`, wird nur dieses Device entfernt. Bricht ein Pflichtstream ab, werden alle Devices dieser Service-ID entfernt. Nach einem Reconnect wird wieder ein vollständiger Snapshot geladen.

## Häufige Rückfragen

### Warum mehrere Methodenstreams?

> „Die Aufrufe bleiben typisiert und verwenden das vorhandene Routingmuster. Die Streams laufen über denselben HTTP/2-Kanal. Ein einzelner multiplexierter Stream würde einen zusätzlichen Dispatcher und schwächer typisierte Nachrichten benötigen.“

### Was passiert bei einer doppelten ServiceId?

Solange eine Service-ID verbunden ist, wird eine zweite Verbindung mit anderer `ConnectionId` abgelehnt. Erst nach vollständigem Cleanup kann sie sich neu verbinden.

### Was passiert bei einer doppelten Device-ID?

Die `LocalDeviceId` muss nur innerhalb einer Service-ID eindeutig sein. Die `IntegrationDeviceId` kombiniert beide Werte und verhindert damit Kollisionen zwischen Integrationen.

## Zusammenfassung für ungefähr eine Minute

> „Das generische Routing wird nach iCore verschoben. Das DeviceIntegrationPlugin ergänzt einen IntegrationDeviceCatalog, die Stream- und Lifecycle-Überwachung sowie die lokale Eventverteilung. Die ServiceDirectory bleibt die einzige Quelle für verbundene Services; der IntegrationDeviceCatalog enthält nur veröffentlichte Devices. Neue Typen beschreiben ihre fachliche Rolle direkt, ohne überall denselben langen Präfix zu wiederholen. Jede konkrete Integration implementiert denselben fachlichen Vertrag und verwendet das Integration SDK für Streams, SmartProxy und Reconnect. Ihre interne Architektur ist nicht Teil des aktuellen Scopes. Endet ein Pflichtstream, wird die vollständige Integration entfernt und nach dem Reconnect über einen neuen Snapshot synchronisiert.“

Durchgehen:

- Plugin.cs als Startpunkt, der die Services startet.
- DeviceIntegrationTransmitters ist ein typisierter Katalog der vom Plugin verwendeten JobTransmitter. Er routet nicht selbst, sondern stellt die passenden generischen Transmitter unter fachlichen Namen bereit.
- WorkerService geht von Integration also Agent zu Plguin und von Plugin zu Integration
- IntegrationStreamTracker: „Er merkt sich, welche Methodenstreams einer Integration geöffnet sind, und erkennt, wann die Integration vollständig bereit ist oder ausfällt.“
- IntegrationStreamLease: „Sie repräsentiert einen geöffneten Stream und meldet beim Dispose zuverlässig an den Tracker, dass dieser Stream beendet wurde.“
- IntegrationDeviceCatalog: Der Catalog enthält nur veröffentlichte Devices.
- DeviceIntegrationService: für Clients

SDK:

- IDeviceIntegration: Das ist die einzige fachliche Schnittstelle, die eine konkrete Integration implementieren muss. Derzeit enthält sie nur GetDevices. Die Integration muss nichts über gRPC, Routing, Worker oder Reconnect wissen.
- DeviceIntegrationHostFactory: öffentlicher SDK Einsstiegspunkt und baut die interne Laufzeit
- DeviceIntegrationRuntime: Die Runtime hält den internen Autofac-Container am Leben. Der Host besitzt die Runtime und gibt sie beim Dispose vollständig frei.
- DeviceIntegrationHost: Er steuert den gesamten Lebenszyklus einer Integration: starten, stoppen und nach einem Verbindungsabbruch mit neuer ConnectionId neu verbinden
- IntegrationWorkerSupervisor: Er überwacht alle Methodenworker einer Verbindung und beendet die gesamte Verbindung, sobald einer dieser Pflichtworker ausfällt.
