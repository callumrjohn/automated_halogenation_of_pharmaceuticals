from opentrons import simulate
from opentrons import protocol_api, types


# metadata
metadata = {
    'protocolName': 'CRJ-01-056',
    'author': 'Callum R. John <crj21@ic.ac.uk>',
    'description': 'Halogenation repeats and high TFA',
    'apiLevel': '2.9'
}

def run(protocol: protocol_api.ProtocolContext):
    
    # labware
    tiprack1 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tiprack2 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    stock96 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 5)
    stock12 = protocol.load_labware('mettlertoledo_12_reservoir_24000ul', 2)
    plate = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 3)

    #tfa and hfip quantities
    hfip_quantities = {'A1': 60, 'A2': 30, 'A4': 36, 'A5': 24, 'A7': 24, 'A9': 60, 'A10': 30, 'A11': 30}
    tfa_dil_quantities = {'A2': 30, 'A3': 60, 'A10': 30}
    tfa_med_quantities = {'A4': 24, 'A5': 36, 'A6': 60, 'A11': 30}
    tfa_conc_quantities = {'A7': 36, 'A8': 60}


    # pipettes
    multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks = [tiprack1, tiprack2])
    protocol.max_speeds['Z'] = 200
    
    def premulti(solution):
        multi.pick_up_tip()
        # Pre-wetting of tip
        for _ in range(2):
            multi.aspirate(100, solution)
            multi.move_to(solution.top())
            protocol.delay(seconds = 5)
            multi.dispense(100, solution.top())
            multi.blow_out()
            
        # Pre-saturation
        multi.move_to(solution.bottom(1))
        multi.mix(2, 100)


    def liq_hand(vol, asp_well, dis_well):
        if count[0] == -1:
            premulti(asp_well)
            count[0] = 0
        if count[0] == 4:
            multi.drop_tip()        
            count[0] = 0
            premulti(asp_well)
                    
        multi.aspirate(vol, asp_well, rate = 0.5)
        multi.touch_tip()
        multi.dispense(vol, dis_well.top(), rate = 0.5)
        multi.blow_out()

        count[0] = count[0] + 1

    def count_check():
        if count[0] != 0:
            multi.drop_tip()
        count = [-1]



    count = [-1]
    
    # substrate dispenses
    
    for wells in plate.rows()[0][:-1]:
        liq_hand(100, stock96['A1'], wells)

    count_check()


    #HFIP dispenses

    for well, vol in hfip_quantities.items():
        liq_hand(vol, stock12['A1'], plate[well])
        
    count_check() 
    
    # TFA dispenses

    for well, vol in tfa_dil_quantities.items():
        liq_hand(vol, stock12['A2'], plate[well])

    count_check()

    
    for well, vol in tfa_med_quantities.items():
        liq_hand(vol, stock12['A3'], plate[well])

    count_check()


    for well, vol in tfa_conc_quantities.items():
        liq_hand(vol, stock12['A4'], plate[well])

    count_check()


    #N-X dispenses
    for wells in plate.rows()[0][:-1]:
        liq_hand(40, stock96['A2'], wells)

    count_check()