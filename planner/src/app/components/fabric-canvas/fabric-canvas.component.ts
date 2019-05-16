import { Component, OnInit, ViewChild, ElementRef, AfterViewInit, OnDestroy } from '@angular/core';
import { fabric } from 'fabric';
import { fromEvent, Subject } from 'rxjs';
import { takeUntil, debounceTime } from 'rxjs/operators';
import { FabricService } from '../../services/fabric.service';

@Component({
  selector: 'app-fabric-canvas',
  templateUrl: './fabric-canvas.component.html',
  styleUrls: ['./fabric-canvas.component.css']
})
export class FabricCanvasComponent implements OnInit, AfterViewInit, OnDestroy {
  canvas: fabric.Canvas;

  // Used to resize the canvas object
  @ViewChild('canvasContainer') canvasContainer: ElementRef;
  private resizeWindow$ = fromEvent(window, 'resize');

  // Used to unsubscribe all subscriptions in the pipe operator
  private ngUnsubscribe$ = new Subject<void>();

  constructor(private fabricService: FabricService) {}

  ngOnInit() {
    this.canvas = new fabric.Canvas('canvas');
    this.canvas.backgroundColor = 'lightgreen';
    this.canvas.renderAll();

    // Update the canvas to match the container size
    this.resizeWindow$
      .pipe(
        debounceTime(300),
        takeUntil(this.ngUnsubscribe$)
      )
      .subscribe(() => {
        this.canvas.setDimensions({
          width: this.canvasContainer.nativeElement.offsetWidth,
          height: this.canvasContainer.nativeElement.offsetHeight
        });
      });

    // Initially get existing fabric objects, later use observables
    Object.values(this.fabricService.objects).forEach(object =>
      this.canvas.add(object)
    );

    // When Fabric objects are added / removed, update the canvas
    this.fabricService.addedFabricObjects$
      .pipe(takeUntil(this.ngUnsubscribe$))
      .subscribe(objects => objects.map(object => this.canvas.add(object)));
    // this.fabricService.removedFabricObjects$
    //   .pipe(takeUntil(this.ngUnsubscribe$))
    //   .subscribe(objects => objects.map(object => this.canvas.remove(object)));
  }

  ngAfterViewInit() {
    // Sets the canvas dimensions during the initial render. Not using the
    // timeout will result in the wrong width being set (scrollbar width)
    setTimeout(
      () =>
        this.canvas.setDimensions({
          width: this.canvasContainer.nativeElement.offsetWidth,
          height: this.canvasContainer.nativeElement.offsetHeight
        }),
      50
    );
  }

  ngOnDestroy() {
    this.ngUnsubscribe$.next();
    this.ngUnsubscribe$.complete();
  }
}
