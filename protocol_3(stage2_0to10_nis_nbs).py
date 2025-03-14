from opentrons import simulate
from opentrons import protocol_api, types


# metadata
metadata = {
    'protocolName': 'protocol_3(stage2_0to10_nis_nbs)',
    'author': 'Callum R. John <crj21@ic.ac.uk>',
    'description': 'Protocol for NIS and NBS screen of substrates across 3 plates',
    'apiLevel': '2.9'
}

def run(protocol: protocol_api.ProtocolContext):
    
    # LABWARE

    # ot_2 tipracks
    tiprack1 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tiprack2 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    tiprack3 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    tiprack4 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)

    
    stock96 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 5)
    stock12 = protocol.load_labware('mettlertoledo_12_reservoir_24000ul', 6)
    plate1 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 7)
    plate2 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 8)
    plate3 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 10)
    
    plates = [plate1, plate2, plate3]
    
    # stocks and dimentions
    substrates = stock96.rows()[0][0:3]
    substrate_vol = 1500 #ul
    sub_height_t0 = substrate_vol/(stock96['A1'].length*stock96['A1'].width)
    sub_depth_t0 = sub_height_t0 - 3

    hfip = stock12.wells()[0]
    hfip_vol = 12000 #ul
    hfip_height_t0 = hfip_vol/(stock12['A1'].length*stock12['A1'].width)
    hfip_depth_t0 = hfip_height_t0 - 3

    tfa_dil = stock12.wells()[1]
    tfa_dil_vol = 5000 #ul
    tfa_dil_height_t0 = tfa_dil_vol/(stock12['A1'].length*stock12['A1'].width)
    tfa_dil_depth_t0 = tfa_dil_height_t0 - 3

    tfa_conc = stock12.wells()[2]
    tfa_conc_vol = 4000 #ul
    tfa_conc_height_t0 = tfa_conc_vol/(stock12['A1'].length*stock12['A1'].width)
    tfa_conc_depth_t0 = tfa_conc_height_t0 - 3

    nbs = stock12.wells()[3]
    nbs_vol = 6200 #ul
    nbs_height_t0 = nbs_vol/(stock12['A1'].length*stock12['A1'].width)
    nbs_depth_t0 = nbs_height_t0 - 3

    nis = stock12.wells()[4]
    nis_vol = 6200 #ul
    nis_height_t0 = nis_vol/(stock12['A1'].length*stock12['A1'].width)
    nis_depth_t0 = nis_height_t0 - 3
    #print(stock12['A1'].length*stock12['A1'].width)

    #counts
    substrate1_count = [0]
    substrate2_count = [0]
    substrate3_count = [0]
    hfip_count = [0]
    tfa_dil_count = [0]
    tfa_conc_count = [0]
    nbs_count = [0]
    nis_count = [0]

    #totals
    sub_total = 12
    hfip_total = 24
    tfa_dil_total = 12
    tfa_conc_total = 18
    nbs_count_total = 18
    nis_count_total = 18


    #tfa and hfip quantities
    hfip_quantities = {'A1': 60, 'A2': 30, 'A3': 0, 'A4': 36, 'A5': 24, 'A6': 0, 'A7': 60, 'A8': 30, 'A9': 0, 'A10': 36, 'A11': 24, 'A12': 0}
    tfa_dil_quantities = {'A1': 0, 'A2': 30, 'A3': 60, 'A4': 0, 'A5': 0, 'A6': 0, 'A7': 0, 'A8': 30, 'A9': 60, 'A10': 0, 'A11': 0, 'A12': 0}
    tfa_conc_quantities = {'A1': 0, 'A2': 0, 'A3': 0, 'A4': 24, 'A5': 36, 'A6': 60, 'A7': 0, 'A8': 0, 'A9': 0, 'A10': 24, 'A11': 36, 'A12': 60}


    # pipettes
    multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks = [tiprack1, tiprack2, tiprack3, tiprack4])
    protocol.max_speeds['Z'] = 60
    
    def premulti(solution, height_t0, well_count, total):
        multi.pick_up_tip()
        # Pre-wetting of tip
        for k in range (2):
            multi.aspirate(100, solution.bottom(height_t0 - height_t0*well_count[0]/total))
            multi.move_to(solution.top())
            protocol.delay(seconds = 5)
            multi.dispense(100, solution.top())
            multi.blow_out()
            
        # Pre-saturation
        multi.move_to(solution.bottom(height_t0 - height_t0*well_count[0]/total))
        multi.mix(2, 100)


    def liq_hand(vol, asp_well, dis_well, height_t0, well_count, total):
        if count[0] == -1:
            premulti(asp_well, height_t0, well_count, total)
            count[0] = 0
        if count[0] == 4:
            multi.drop_tip()        
            count[0] = 0
            premulti(asp_well, height_t0, well_count, total)
                    
        well_count[0] = well_count[0] + 1
        multi.aspirate(vol, asp_well.bottom(height_t0 - height_t0*well_count[0]/total), rate = 0.5)
        multi.dispense(vol, dis_well.top(), rate = 0.5)
        multi.blow_out()
        #print(height_t0 - height_t0*well_count[0]/total)

        count[0] = count[0] + 1


    count = [-1]
    
    # substrate(plate 1) dispenses
    for wells in plate1.rows()[0]:
        liq_hand(100, substrates[0], wells, sub_depth_t0, substrate1_count, sub_total)

    if count[0] != 0:
        multi.drop_tip()
    count = [-1]

    #substrate(plate 2) dispenses
    for wells in plate2.rows()[0]:
        liq_hand(100, substrates[1], wells, sub_depth_t0, substrate2_count, sub_total)

    if count[0] != 0:
        multi.drop_tip()
    count = [-1]

    #substrate(plate 3) dispenses
    for wells in plate3.rows()[0]:
        liq_hand(100, substrates[2], wells, sub_depth_t0, substrate3_count, sub_total)

    if count[0] != 0:
        multi.drop_tip()
    count = [-1]

    #HFIP dispenses
    for plate in plates:
        for well, vol in hfip_quantities.items():
            if vol != 0:
                liq_hand(vol, hfip, plate[well], hfip_depth_t0, hfip_count, hfip_total)
        
    if count[0] != 0:
        multi.drop_tip()
    count = [-1]  
    
    # TFA dilute dispenses
    for plate in plates:
        for well, vol in tfa_dil_quantities.items():
            if vol != 0:
                liq_hand(vol, tfa_dil, plate[well], tfa_dil_depth_t0, tfa_dil_count, tfa_dil_total)

    if count[0] != 0:
        multi.drop_tip()
    count = [-1]

    #TFA conc dispenses
    for plate in plates:
        for well, vol in tfa_conc_quantities.items():
            if vol != 0:
                liq_hand(vol, tfa_conc, plate[well], tfa_conc_depth_t0, tfa_conc_count, tfa_conc_total)
    
    if count[0] != 0:
        multi.drop_tip()
    count = [-1]

    #NBS dispenses
    for plate in plates:
        for well in plate.rows()[0][0:6]:
            liq_hand(40, nbs, well, nbs_depth_t0, nbs_count, nbs_count_total)
    
    if count[0] != 0:
        multi.drop_tip()
    count = [-1]

    #NIS dispenses
    for plate in plates:
        for well in plate.rows()[0][6:12]:
            liq_hand(40, nis, well, nis_depth_t0, nis_count, nis_count_total)

    if count[0] != 0:
        multi.drop_tip()
    count = [-1]

    # python.exe -m opentrons.simulate "C:\Users\crj21\OneDrive - Imperial College London\PhD\1st Year\CRJ-01-050\crj_01_050_protocol.py" --custom-labware-path="C:\Users\crj21\AppData\Roaming\Opentrons\labware"