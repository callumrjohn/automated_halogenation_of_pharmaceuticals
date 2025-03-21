from opentrons import protocol_api


# metadata
metadata = {
    'protocolName': 'protocol_1(stage1_screening)',
    'author': 'Callum R. John <crj21@ic.ac.uk>',
    'description': 'Protocol for broad screen of substrates across 2 plates',
    'apiLevel': '2.9'
}

def run(protocol: protocol_api.ProtocolContext):
    
    # LABWARE

    # Pipette tip racks
    tiprack1 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tiprack2 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    tiprack3 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    tiprack4 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)

    # Stock solution plates
    stock96 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 5)
    stock12 = protocol.load_labware('mettlertoledo_12_reservoir_24000ul', 6)

    # Reaction plates
    plate1 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 7)
    plate2 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 8)
    plate3 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 10)
    plate4 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 11)
    plates = [plate1, plate2, plate3, plate4]
    
    # pipettes
    multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks = [tiprack1, tiprack2, tiprack3, tiprack4])



    # STOCK SOLUTIONS

    substrates = stock96.rows()[0][0:4] # Substrate stock solution locations - A1, B1, C1, D1: The first four columns of the stock96 plate
    tfa = stock12.wells()[0:3] # HFIP and TFA solution locations
    halogens = stock12.wells()[3:7] # Halogenating reagent locations


    def premulti(solution):
        protocol.max_speeds['Z'] = 200
        multi.pick_up_tip()
        
        # Pre-wetting of tip
        for k in range (2):
            multi.aspirate(100, solution)
            multi.move_to(solution.top())
            protocol.delay(seconds = 5)
            multi.dispense(100, solution.top())
            multi.blow_out()
            
        # Pre-saturation
        multi.move_to(solution.bottom(1))
        multi.mix(2, 100)
            
        protocol.max_speeds['Z'] = 80


    def liq_hand(vol, asp_well, dis_well):
        if count[0] == -1:
            premulti(asp_well)
            count[0] = 0
        if count[0] == 4:
            multi.drop_tip()        
            count[0] = 0
            premulti(asp_well)
                    
        multi.aspirate(vol, asp_well, rate = 0.5)
        multi.dispense(vol, dis_well.top(), rate = 0.5)
        multi.blow_out()

        count[0] = count[0] + 1

    # substrate dispenses
    
    for substrate, plate in zip(substrates, plates):
        for j in range(12):
            liq_hand(100, substrate, plate.rows()[0][j])

    if count[0] != 0:
        multi.drop_tip()
    count = [-1]

    # TFA/HFIP dispenses

    for i, acid in enumerate(tfa):
        for plate in plates:
            for j in range(4):
                liq_hand(60, acid, plate.rows()[0][3*j+i])

    if count[0] != 0:
        multi.drop_tip()
    count = [-1]

    # halogenating reagent dispenses
    for i, halogen in enumerate(halogens):
        for plate in plates:
            for j in range(3):
                liq_hand(40, halogen, plate.rows()[0][3*i+j])
        
    if count[0] != 0:
        multi.drop_tip()
    count = [-1]
