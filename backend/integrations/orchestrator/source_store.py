import hashlib
import json

from ops.models import SourceRecord


class SourceRecordStore:
    def upsert(self, source: str, external_id: str, raw_payload: dict) -> tuple[SourceRecord, bool]:
        """
        Upsert a SourceRecord by (source, external_id).
        Compute SHA-256 checksum of json.dumps(raw_payload, sort_keys=True).
        If checksum unchanged from stored record: return (record, False) — skip processing.
        If new or changed: save record, return (record, True).
        """
        checksum = hashlib.sha256(json.dumps(raw_payload, sort_keys=True).encode()).hexdigest()
        record, created = SourceRecord.objects.get_or_create(
            source=source,
            external_id=str(external_id),
            defaults={'raw_payload': raw_payload, 'payload_checksum': checksum},
        )
        if not created:
            if record.payload_checksum == checksum:
                return record, False
            record.raw_payload = raw_payload
            record.payload_checksum = checksum
            record.save(update_fields=['raw_payload', 'payload_checksum', 'last_seen_at'])
        return record, True
