from opentrons import simulate
from opentrons import protocol_api, types


# metadata
metadata = {
    'protocolName': 'protocol_2(stage2_0to6_chlor)',
    'author': 'Callum R. John <crj21@ic.ac.uk>',
    'description': 'Protocol for screening eight substrates against various acid equivalents',
    'apiLevel': '2.9'
}

def run(protocol: protocol_api.ProtocolContext):
    
    # LABWARE
    tiprack1 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tiprack2 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    
    stock8 = protocol.load_labware('mettlertoledo_8_reservoir_36000ul', 2)
    stock12 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 5)
    
    plate = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 3)

    # pipettes
    multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks = [tiprack1, tiprack2])

    protocol.max_speeds['X'] = 200
    protocol.max_speeds['Y'] = 200


    # volumes:
    # Substrate: 100 uL
    # NCS: 40 uL

    acid_no = {0: {'stock': None, 'vol': 0}, 2: {'stock': None, 'vol': 0}}
    
    acid_0 = {3: {'stock': stock12['A6'], 'vol': 40}}
    
    acid_1 = {4: {'stock': stock12['A7'], 'vol': 20}, 
              5: {'stock': stock12['A7'], 'vol': 40},
              6: {'stock': stock12['A7'], 'vol': 60}}
    
    acid_2 = {1: {'stock': stock12['A8'], 'vol': 20}, 
              7: {'stock': stock12['A8'], 'vol': 20},
              8: {'stock': stock12['A8'], 'vol': 30},
              9: {'stock': stock12['A8'], 'vol': 40},
              10: {'stock': stock12['A8'], 'vol': 50},
              11: {'stock': stock12['A8'], 'vol': 60}}

    acid = {}
    acid.update(acid_no)
    acid.update(acid_0)
    acid.update(acid_1)
    acid.update(acid_2)
    
    aciddis = [acid_0, acid_1, acid_2]

    
    # acid equivalents (3-11): 0.1, 0.5, 1, 1.5, 2, 3, 4, 5, 6
    

    def premulti(solution): # is the solution viscous? (no = 0, yes = 1)
        protocol.max_speeds['Z'] = 200
        multi.pick_up_tip()
        
        # Pre-wetting of tip
        for k in range (2):
            multi.aspirate(100, solution)
            multi.move_to(solution.top())
            protocol.delay(seconds = 5)
            multi.dispense(100, solution.top())
            
        # Pre-saturation
        multi.move_to(solution.bottom(1))
        multi.mix(2, 100)
            
        protocol.max_speeds['Z'] = 50


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

        
    # dispense
    count = [-1]
    
    # substrate
    for i in range(12):
        liq_hand(100, stock8['A1'], plate.rows()[0][i])

    if count[0] != 0:
        multi.drop_tip()
    count = [-1]


    # HFIP
    for wells in acid:
        if wells == 0 or wells == 1:
            extra = 40
        else:
            extra = 0
        
        if acid[wells]['vol'] < 60:
            liq_hand(60 - acid[wells]['vol'] + extra, stock12['A5'], plate.rows()[0][wells])

    if count[0] != 0:
        multi.drop_tip()
    count = [-1]


    # Acid
    for acids in aciddis:
        for wells in acids:
            liq_hand(acid[wells]['vol'], acid[wells]['stock'], plate.rows()[0][wells])
        
        if count[0] != 0:
            multi.drop_tip()
        count = [-1]


    # NCS
    for i in range(10):
        liq_hand(40, stock12.wells()[0], plate.rows()[0][i+2])
        
    if count[0] != 0:
        multi.drop_tip()