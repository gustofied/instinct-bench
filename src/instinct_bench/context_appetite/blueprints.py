from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Blueprint:
    title: str
    entity_label: str
    entity_prefix: str
    event_noun: str

    def question(self, event_id: str) -> str:
        return f"Which {self.entity_label} controlled {self.event_noun} {event_id}?"


BLUEPRINTS: tuple[Blueprint, ...] = (
    Blueprint("Deployment Recovery", "deployment", "dep", "recovery event"),
    Blueprint("Capacity Quote", "capacity feed", "feed", "quote correction"),
    Blueprint("Tenant Credential", "tenant credential", "cred", "access event"),
    Blueprint("Invoice Rollback", "release", "rel", "invoice recovery"),
    Blueprint("Reservation Routing", "allocation endpoint", "alloc", "reservation"),
    Blueprint("Power Transfer", "power circuit", "circuit", "transfer event"),
    Blueprint("Network Failover", "network route", "route", "failover"),
    Blueprint("Cooling Alarm", "cooling loop", "loop", "alarm"),
    Blueprint("Hardware Shipment", "shipment lot", "lot", "receipt"),
    Blueprint("Compliance Exception", "control", "ctrl", "exception"),
    Blueprint("Contract Pricing", "contract amendment", "amd", "price change"),
    Blueprint("Meter Reconciliation", "billing meter", "meter", "reconciliation"),
    Blueprint("Rack Inventory", "GPU rack", "rack", "inventory correction"),
    Blueprint("Maintenance Incident", "maintenance window", "mw", "incident"),
    Blueprint("Carbon Accounting", "certificate", "cert", "accounting entry"),
    Blueprint("Storage Recovery", "storage volume", "vol", "recovery event"),
    Blueprint("Firmware Regression", "firmware bundle", "fw", "regression"),
    Blueprint("DNS Incident", "origin cluster", "origin", "routing incident"),
    Blueprint("Access Review", "access credential", "key", "review finding"),
    Blueprint("Settlement Error", "settlement batch", "batch", "ledger correction"),
    Blueprint("Support Escalation", "support queue", "queue", "escalation"),
)

DEV_BLUEPRINTS = BLUEPRINTS[:6]
EVAL_BLUEPRINTS = BLUEPRINTS[6:]
