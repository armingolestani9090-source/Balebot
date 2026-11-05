from bale import BaleClient, pb
from config import BALE_ACCESS_TOKEN

client = BaleClient(BALE_ACCESS_TOKEN)

print("pb.GroupPeer:")
print(pb.GroupPeer)

print()

print("GroupPeer fields:")

for field in pb.GroupPeer.DESCRIPTOR.fields:
    print(
        field.name,
        "| type:",
        field.type,
        "| message:",
        field.message_type.full_name
        if field.message_type
        else None
    )