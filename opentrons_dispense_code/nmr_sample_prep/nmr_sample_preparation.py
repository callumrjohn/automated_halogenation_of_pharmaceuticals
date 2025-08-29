from opentrons import protocol_api


# metadata
metadata = {
    'protocolName': 'nmr_sample_preparation',
    'author': 'Callum R. John <crj21@ic.ac.uk>',
    'description': 'Protocol for preparing DMSO-d6 NMR samples from crude residues within a 96-well reaction plate',
    'apiLevel': '2.9'
}

def run(protocol: protocol_api.ProtocolContext):
    
    # LABWARE

    # Pipette tip racks
    tiprack1 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    tiprack2 = protocol.load_labware('opentrons_96_tiprack_300ul', 8)

    # Stock solution plate
    dmso = protocol.load_labware('acme_2_reservoir_120000ul', 5) # DMSO-d6 containing plate. A1 - Internal standard + DMSO-d6, A2 - Neat DMSO-d6

    # Stock solution well plate dimentions for internal standard stock soltuion dispense 
    dmso_x = 5.59 # mm
    dmso_y = 7.54 # mm
    dmso_vol = 59 # mL - total volume of stock used (inc. grace volume) for a 96-well plate. Can be changed accordingly
    dmso_z = 10*dmso_vol/(dmso_x*dmso_y)-3 # mm - calculate the height of the stock solution in the well
    
    # Reaction plate containing crude samples
    plate = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 6)
    dpw = 3 # number of dispenses per well
    columns = 12 # number of columns to dispense over within the reaction plate (begining at column 1). Change if plate is only partially full
    total_count = dpw*columns # calculate the total number of dispenses for the run

    # Pipette
    multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks = [tiprack1, tiprack2])
    count = 0 # Running tally of the total number of dispenses
    
    # DISPENSE PROTOCOL
    
    wells = plate.rows()[0] # A1 - A12

    # Internal standard stock solution dispense
    for well in wells:
        multi.pick_up_tip()
        for j in range(dpw): 
            if dmso_z - dmso_z*count/total_count < 0: # Check to ensure the z-value for .bottom(z) is no negative, which would result in tip collision with the well bottom
                pass
            count += 1
            multi.aspirate(200, dmso['A1'].bottom(dmso_z - dmso_z*count/total_count)) # Dispense 200 uL x number of dispenses per well across the plate
            multi.dispense(200, well.top())
            multi.blow_out()
        multi.drop_tip()
    
    # DMSO-d6 top up (to ensure solvation of crude)
    multi.pick_up_tip()
    for well in wells:
        multi.aspirate(250, dmso['A2']) # Dispense 250 uL of neat DMSO-d6 into each well across the plate
        multi.dispense(250, well.top())
        multi.blow_out()
    multi.drop_tip()