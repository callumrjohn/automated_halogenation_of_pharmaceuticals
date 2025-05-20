from opentrons import protocol_api, types


# metadata
metadata = {
    'protocolName': 'nmr_sample_transfer',
    'author': 'Callum R. John <crj21@ic.ac.uk>',
    'description': 'Protocol for transfering NMR solutions from reaction plate to a rack of HT NMR tubes',
    'apiLevel': '2.9'
}

def run(protocol: protocol_api.ProtocolContext):
    
    # LABWARE

    # Pipette tip rack
    tiprack1 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)

    # Plate containing NMR samples
    plate = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 5)

    # Tube rack with HT 5 mm NMR tubes
    rack = protocol.load_labware('nmr_96_tuberack_1000ul', 6) # 3D printed tube rack. See labware folder in repo for .stl files

    # Pipette
    multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks = [tiprack1])

    # Reaction plate dimentions for sample transfer
    sample_vol = 850 #ul
    sample_height_t0 = sample_vol/(plate['A1'].length*plate['A1'].width) # Call plate dimentions and caluclate starting height of samples
    sample_depth_t0 = sample_height_t0 - 3 # subtract 3 mm to ensure pipette tip submersion

    # DISPENSE PROTOCOL

    for well, tube in zip(plate.rows()[0], rack.rows()[0]):
        multi.pick_up_tip()
        multi.mix(10, 150, location = well.bottom(2), rate = 2) # Mix the ssample before transfer to ensure homogeneity
        
        dispense_point = tube.top().move(types.Point(x=3.8/2, y=0, z=-3)) # 
        for i in range(3):

            multi.aspirate(250, well.bottom(sample_depth_t0-sample_depth_t0*(i+1)/3))
            multi.move_to(tube.top())
            multi.dispense(250, dispense_point)
            multi.blow_out()
        
        multi.drop_tip()