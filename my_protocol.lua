-- UDPKS2 Protocol Dissector for Wireshark

-- Create a new protocol
udpks2_proto = Proto("UDPKS2", "UDPKS2 Protocol")

-- Define protocol fields
local flags_field = ProtoField.uint8("udpk2.flags", "Flags", base.HEX)
local seq_number_field = ProtoField.uint16("udpk2.seq_number", "Sequence Number")
local crc_field = ProtoField.uint16("udpk2.crc", "CRC")
local data_field = ProtoField.bytes("udpk2.data", "Data")

-- Add fields to the protocol
udpks2_proto.fields = {flags_field, seq_number_field, crc_field, data_field}

-- Dissector function
function udpks2_proto.dissector(buffer, pinfo, tree)
    -- Validate packet length
    if buffer:len() < 6 then
        return
    end

    -- Create a subtree for the UDPKS2 protocol
    local subtree = tree:add(udpks2_proto, buffer(), "UDPKS2 Protocol Data")

    -- Add protocol fields to the subtree
    local flags = buffer(0, 1):uint()
    local flag_string = ""
    if bit32.band(flags, 0x80) ~= 0 then flag_string = flag_string .. "[E]" end
    if bit32.band(flags, 0x40) ~= 0 then flag_string = flag_string .. "[T]" end
    if bit32.band(flags, 0x20) ~= 0 then flag_string = flag_string .. "[F]" end
    if bit32.band(flags, 0x10) ~= 0 then flag_string = flag_string .. "[A]" end
    if bit32.band(flags, 0x08) ~= 0 then flag_string = flag_string .. "[R]" end
    if bit32.band(flags, 0x04) ~= 0 then flag_string = flag_string .. "[S]" end
    if bit32.band(flags, 0x02) ~= 0 then flag_string = flag_string .. "[Q]" end
    if bit32.band(flags, 0x01) ~= 0 then flag_string = flag_string .. "[K]" end

    local seq_number = buffer(1, 2):uint()
    local crc = buffer(3, 2):uint()

    subtree:add(flags_field, buffer(0, 1)):append_text(" " .. flag_string)
    subtree:add(seq_number_field, buffer(1, 2))
    subtree:add(crc_field, buffer(3, 2))

    -- Add data to the subtree as bytes
    local data_subtree = subtree:add(data_field, buffer(5, buffer:len() - 5))

end

-- Register the dissector
udp_table = DissectorTable.get("udp.port")
udp_table:add(42069, udpks2_proto)
